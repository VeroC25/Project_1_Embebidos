#!/usr/bin/env python3

from pathlib import Path
import sys


APP = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else "prueba_integrada_h1.py"
)

RESULTADOS = Path("resultados")
RESULTADOS.mkdir(
    parents=True,
    exist_ok=True
)

REPORTE = RESULTADOS / "E1_bus_watch_rpi.txt"


if not APP.exists():

    print(
        f"FAIL: no existe {APP}"
    )

    raise SystemExit(1)


codigo = APP.read_text(
    encoding="utf-8"
)


pruebas = {
    "Obtencion del bus":
        "pipeline.get_bus()" in codigo,

    "Signal watch":
        "bus.add_signal_watch()" in codigo,

    "Conexion del manejador":
        'bus.connect(' in codigo
        and '"message"' in codigo
        and "manejar_mensaje" in codigo,

    "Manejo de ERROR":
        "Gst.MessageType.ERROR" in codigo,

    "Manejo de WARNING":
        "Gst.MessageType.WARNING" in codigo,

    "Manejo de EOS":
        "Gst.MessageType.EOS" in codigo,
}


lineas = [
    "E1 - WATCH DEL BUS DE GSTREAMER",
    "",
]


for nombre, resultado in pruebas.items():

    estado = (
        "PASS"
        if resultado
        else "FAIL"
    )

    lineas.append(
        f"[{estado}] {nombre}"
    )


ok = all(
    pruebas.values()
)


lineas.append("")


if ok:

    lineas.append(
        "PASS: el pipeline tiene un watch "
        "del bus y atiende ERROR, WARNING y EOS."
    )

else:

    lineas.append(
        "FAIL: falta al menos un requisito "
        "del manejo del bus."
    )


REPORTE.write_text(
    "\n".join(lineas) + "\n",
    encoding="utf-8"
)


print(
    "\n".join(lineas)
)

print()
print(
    f"Evidencia: {REPORTE}"
)


if not ok:

    raise SystemExit(1)


print()
print("========================================")
print(" TEST E1 BUS WATCH: PASS")
print("========================================")
