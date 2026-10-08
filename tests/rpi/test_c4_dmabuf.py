#!/usr/bin/env python3

from pathlib import Path
import subprocess
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

REPORTE = RESULTADOS / (
    "C4_dmabuf_rpi.txt"
)

LIBCAMERA_LOG = RESULTADOS / (
    "C4_libcamerasrc_inspect_rpi.log"
)

V4L2SRC_LOG = RESULTADOS / (
    "C4_v4l2src_inspect_rpi.log"
)

HW_LOG = RESULTADOS / (
    "C4_v4l2h264enc_inspect_rpi.log"
)


def inspeccionar(elemento, archivo):

    proceso = subprocess.run(
        [
            "gst-inspect-1.0",
            elemento,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    archivo.write_text(
        proceso.stdout,
        encoding="utf-8"
    )

    return (
        proceso.returncode,
        proceso.stdout,
    )


codigo = APP.read_text(
    encoding="utf-8"
)


rc_libcamera, info_libcamera = (
    inspeccionar(
        "libcamerasrc",
        LIBCAMERA_LOG,
    )
)

rc_v4l2src, info_v4l2src = (
    inspeccionar(
        "v4l2src",
        V4L2SRC_LOG,
    )
)

rc_hw, info_hw = (
    inspeccionar(
        "v4l2h264enc",
        HW_LOG,
    )
)


usa_libcamera = (
    "libcamerasrc" in codigo
)

libcamera_capture_io = (
    "capture-io-mode"
    in info_libcamera
)

v4l2_capture_io = (
    "capture-io-mode"
    in info_v4l2src
)

v4l2_dmabuf = (
    "dmabuf"
    in info_v4l2src.lower()
)

hw_io_mode = (
    "output-io-mode"
    in info_hw
)

hw_dmabuf = (
    "dmabuf"
    in info_hw.lower()
)


# Copias/conversiones actuales del pipeline.
opencv_bgr = (
    "video/x-raw,format=BGR"
    in codigo
)

numpy_copy = (
    ").copy()"
    in codigo
    or
    ".copy()"
    in codigo
)

encoder_nv12 = (
    "video/x-raw,format=NV12"
    in codigo
)

videoconvert_count = (
    codigo.count(
        '"videoconvert ! "'
    )
)


lineas = [
    "C4 - COPIAS Y DMABUF",
    "",
    f"Fuente final usa libcamerasrc: {usa_libcamera}",
    (
        "libcamerasrc expone capture-io-mode: "
        f"{libcamera_capture_io}"
    ),
    (
        "v4l2src expone capture-io-mode: "
        f"{v4l2_capture_io}"
    ),
    (
        "v4l2src anuncia DMABUF: "
        f"{v4l2_dmabuf}"
    ),
    (
        "v4l2h264enc expone output-io-mode: "
        f"{hw_io_mode}"
    ),
    (
        "v4l2h264enc anuncia DMABUF: "
        f"{hw_dmabuf}"
    ),
    "",
    "Copias/conversiones observadas:",
    (
        "[PASS] Rama OpenCV convierte a BGR."
        if opencv_bgr
        else
        "[FAIL] No se encontro la conversion BGR."
    ),
    (
        "[PASS] El callback realiza copia a memoria "
        "de CPU para NumPy/OpenCV."
        if numpy_copy
        else
        "[FAIL] No se identifico la copia del frame."
    ),
    (
        "[PASS] Rama del encoder convierte a NV12."
        if encoder_nv12
        else
        "[FAIL] No se encontro formato NV12."
    ),
    (
        f"videoconvert declarados en el pipeline: "
        f"{videoconvert_count}"
    ),
    "",
]


if usa_libcamera and not libcamera_capture_io:

    lineas.extend(
        [
            "Conclusion sobre capture-io-mode=dmabuf:",
            (
                "La fuente final es libcamerasrc y la "
                "propiedad capture-io-mode no aparece "
                "en su gst-inspect. Por tanto no se "
                "fuerza una propiedad de v4l2src que "
                "no pertenece a la fuente final."
            ),
            "",
        ]
    )


lineas.extend(
    [
        "Revision:",
        (
            "La rama QR necesita memoria accesible "
            "por CPU para OpenCV, por lo que existe "
            "una copia explicita del frame."
        ),
        (
            "La rama H264 contiene videoconvert hacia "
            "NV12. Si el encoder hardware expone "
            "un modo DMABUF/import, queda identificado "
            "como posible optimizacion futura."
        ),
        "",
        "PASS: se revisaron y documentaron las "
        "copias entre dominios de memoria y la "
        "aplicabilidad de DMABUF.",
        "",
        "Evidencias:",
        str(LIBCAMERA_LOG),
        str(V4L2SRC_LOG),
        str(HW_LOG),
    ]
)


REPORTE.write_text(
    "\n".join(lineas) + "\n",
    encoding="utf-8"
)

print(
    "\n".join(lineas)
)


if not (
    usa_libcamera
    and opencv_bgr
    and numpy_copy
    and encoder_nv12
):

    raise SystemExit(1)


print()
print("========================================")
print(" TEST C4 DMABUF/COPIAS: PASS")
print("========================================")
