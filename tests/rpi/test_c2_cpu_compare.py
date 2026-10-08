#!/usr/bin/env python3

from pathlib import Path
import os
import signal
import subprocess
import sys
import time


DURACION = int(
    sys.argv[1]
    if len(sys.argv) > 1
    else "60"
)

if DURACION < 60:
    print(
        "FAIL: C2 requiere al menos 60 s "
        "de medicion por encoder."
    )
    raise SystemExit(1)


RESULTADOS = Path("resultados")

RESULTADOS.mkdir(
    parents=True,
    exist_ok=True
)

REPORTE = RESULTADOS / (
    "C2_cpu_compare_rpi.txt"
)

LOG_SW = RESULTADOS / (
    "C2_x264_software_rpi.log"
)

LOG_HW = RESULTADOS / (
    "C2_v4l2_hardware_rpi.log"
)


DEVICE = (
    RESULTADOS
    / "C1_hw_device.txt"
).read_text(
    encoding="utf-8"
).strip()


FORMATO = (
    RESULTADOS
    / "C1_hw_format.txt"
).read_text(
    encoding="utf-8"
).strip()


CLK_TCK = os.sysconf(
    os.sysconf_names["SC_CLK_TCK"]
)


def cpu_seconds(pid):

    datos = Path(
        f"/proc/{pid}/stat"
    ).read_text(
        encoding="utf-8"
    ).split()

    utime = int(datos[13])
    stime = int(datos[14])

    return (
        utime + stime
    ) / CLK_TCK


def medir(nombre, comando, log_path):

    print()
    print(
        f"Iniciando medicion: {nombre}"
    )

    with open(
        log_path,
        "w",
        encoding="utf-8"
    ) as log:

        proceso = subprocess.Popen(
            comando,
            stdout=log,
            stderr=subprocess.STDOUT,
        )

        # Warm-up.
        time.sleep(5)

        if proceso.poll() is not None:
            raise RuntimeError(
                f"{nombre} termino durante warm-up."
            )

        cpu_inicio = cpu_seconds(
            proceso.pid
        )

        t_inicio = time.monotonic()

        time.sleep(DURACION)

        if proceso.poll() is not None:
            raise RuntimeError(
                f"{nombre} termino durante la medicion."
            )

        cpu_fin = cpu_seconds(
            proceso.pid
        )

        t_fin = time.monotonic()

        proceso.send_signal(
            signal.SIGINT
        )

        try:
            proceso.wait(
                timeout=15
            )

        except subprocess.TimeoutExpired:

            proceso.kill()
            proceso.wait()


    tiempo = (
        t_fin - t_inicio
    )

    cpu = (
        cpu_fin - cpu_inicio
    )

    porcentaje = (
        cpu / tiempo
    ) * 100.0

    print(
        f"{nombre}: "
        f"{porcentaje:.2f} % CPU"
    )

    return porcentaje


base = [
    "gst-launch-1.0",
    "-q",
    "libcamerasrc",
    "!",
    "video/x-raw,width=1280,height=720,framerate=30/1",
    "!",
    "videoconvert",
    "!",
    f"video/x-raw,format={FORMATO}",
    "!",
]


cmd_sw = (
    base
    + [
        "x264enc",
        "tune=zerolatency",
        "bitrate=2000",
        "speed-preset=veryfast",
        "key-int-max=30",
        "!",
        "h264parse",
        "!",
        "fakesink",
        "sync=false",
    ]
)


cmd_hw = (
    base
    + [
        "v4l2h264enc",
        f"device={DEVICE}",
        "!",
        "h264parse",
        "!",
        "fakesink",
        "sync=false",
    ]
)


try:

    cpu_sw = medir(
        "x264enc software",
        cmd_sw,
        LOG_SW,
    )

    time.sleep(3)

    cpu_hw = medir(
        "v4l2h264enc hardware",
        cmd_hw,
        LOG_HW,
    )

except Exception as error:

    print(
        f"FAIL: {error}"
    )

    raise SystemExit(1)


if cpu_hw <= 0.01:

    razon = float("inf")

else:

    razon = (
        cpu_sw / cpu_hw
    )


criterio = (
    razon >= 5.0
)


lineas = [
    "C2 - CPU SOFTWARE VS HARDWARE",
    "",
    "Condiciones iguales:",
    "  Resolucion: 1280x720",
    "  Framerate: 30 fps",
    f"  Formato raw: {FORMATO}",
    f"  Duracion medida: {DURACION} s por encoder",
    "",
    f"CPU x264enc software: {cpu_sw:.2f} %",
    f"CPU v4l2h264enc hardware: {cpu_hw:.2f} %",
    (
        "Razon software/hardware: infinito"
        if razon == float("inf")
        else
        f"Razon software/hardware: {razon:.2f}x"
    ),
    "",
    (
        "PASS: razon >= 5x a favor del hardware."
        if criterio
        else
        "FAIL: la razon medida es menor a 5x."
    ),
]


REPORTE.write_text(
    "\n".join(lineas) + "\n",
    encoding="utf-8"
)

print()
print(
    "\n".join(lineas)
)

print()
print("Evidencias:")
print(REPORTE)
print(LOG_SW)
print(LOG_HW)


if not criterio:
    raise SystemExit(1)


print()
print("========================================")
print(" TEST C2 CPU: PASS")
print("========================================")
