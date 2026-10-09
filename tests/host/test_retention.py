#!/usr/bin/env python3

import ast
import os
import tempfile

from datetime import datetime


APP = "prueba_integrada_h1.py"


# ============================================================
# CARGAR SOLO LA LOGICA DE RETENCION DE LA APLICACION
# ============================================================

with open(APP, "r", encoding="utf-8") as archivo:
    codigo = archivo.read()

arbol = ast.parse(codigo)

nodos = []

for nodo in arbol.body:

    # Recuperar las constantes de retencion.
    if isinstance(nodo, ast.Assign):

        nombres = [
            objetivo.id
            for objetivo in nodo.targets
            if isinstance(objetivo, ast.Name)
        ]

        if (
            "DIAS_RETENCION_VIDEO" in nombres
            or "DIAS_RETENCION_BITACORA" in nombres
        ):
            nodos.append(nodo)

    # Recuperar las funciones reales de limpieza.
    if isinstance(nodo, ast.FunctionDef):

        if nodo.name in (
            "limpiar_evidencias_antiguas",
            "limpiar_bitacora_antigua",
        ):
            nodos.append(nodo)


modulo_retencion = ast.Module(
    body=nodos,
    type_ignores=[]
)

ast.fix_missing_locations(modulo_retencion)


namespace = {
    "os": os,
    "datetime": datetime,
}

exec(
    compile(
        modulo_retencion,
        APP,
        "exec"
    ),
    namespace
)


# ============================================================
# FIJAR FECHA DE PRUEBA
# ============================================================

class FechaPrueba(datetime):

    @classmethod
    def now(cls, tz=None):
        return cls(
            2026,
            10,
            5,
            12,
            0,
            0
        )


namespace["datetime"] = FechaPrueba


# ============================================================
# VALIDAR CONFIGURACION
# ============================================================

assert namespace["DIAS_RETENCION_VIDEO"] == 7
assert namespace["DIAS_RETENCION_BITACORA"] == 30

print("PASS: politica configurada en 7 y 30 dias.")


# ============================================================
# CREAR ENTORNO TEMPORAL
# ============================================================

with tempfile.TemporaryDirectory() as temporal:

    carpeta_evidencias = os.path.join(
        temporal,
        "evidencias"
    )

    os.makedirs(
        carpeta_evidencias
    )

    archivo_bitacora = os.path.join(
        temporal,
        "bitacora_accesos.log"
    )

    namespace["CARPETA_EVIDENCIAS"] = carpeta_evidencias
    namespace["ARCHIVO_BITACORA"] = archivo_bitacora


    # ========================================================
    # PRUEBA DE VIDEOS
    # ========================================================

    video_viejo = os.path.join(
        carpeta_evidencias,
        "evidencia_2026-09-28_12-00-00_000000.mp4"
    )

    video_reciente = os.path.join(
        carpeta_evidencias,
        "evidencia_2026-09-29_12-00-00_000000.mp4"
    )

    with open(video_viejo, "w", encoding="utf-8"):
        pass

    with open(video_reciente, "w", encoding="utf-8"):
        pass


    namespace[
        "limpiar_evidencias_antiguas"
    ]()


    if os.path.exists(video_viejo):
        raise AssertionError(
            "FAIL: el video con 7 dias "
            "no fue eliminado."
        )

    if not os.path.exists(video_reciente):
        raise AssertionError(
            "FAIL: se elimino un video reciente."
        )

    print(
        "PASS: retencion de videos "
        "funciona correctamente."
    )


    # ========================================================
    # PRUEBA DE BITACORA
    # ========================================================

    with open(
        archivo_bitacora,
        "w",
        encoding="utf-8"
    ) as archivo:

        archivo.write(
            "2026-09-05 12:00:00 | "
            "ID: VIEJO | "
            "RESULTADO: DENEGADO\n"
        )

        archivo.write(
            "2026-09-06 12:00:00 | "
            "ID: RECIENTE | "
            "RESULTADO: AUTORIZADO\n"
        )

        archivo.write(
            "LINEA SIN FORMATO "
            "QUE DEBE CONSERVARSE\n"
        )


    namespace[
        "limpiar_bitacora_antigua"
    ]()


    with open(
        archivo_bitacora,
        "r",
        encoding="utf-8"
    ) as archivo:

        contenido = archivo.read()


    if "ID: VIEJO" in contenido:
        raise AssertionError(
            "FAIL: el evento con 30 dias "
            "no fue eliminado."
        )

    if "ID: RECIENTE" not in contenido:
        raise AssertionError(
            "FAIL: se elimino un evento reciente."
        )

    if "LINEA SIN FORMATO" not in contenido:
        raise AssertionError(
            "FAIL: se elimino una linea desconocida."
        )

    print(
        "PASS: retencion de bitacora "
        "funciona correctamente."
    )


print()
print("========================================")
print(" TEST H7 RETENCION: PASS")
print("========================================")
