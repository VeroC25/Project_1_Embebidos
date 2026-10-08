#!/usr/bin/env python3

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import ast
import sys
import time


APP = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else "prueba_integrada_h1.py"
)

RESULTADOS = Path("resultados")
RESULTADOS.mkdir(parents=True, exist_ok=True)

REPORTE = RESULTADOS / "H2_timeout_failsecure.txt"

codigo = APP.read_text(encoding="utf-8")
arbol = ast.parse(codigo)


# ============================================================
# LEER TIMEOUT DE PRODUCCION
# ============================================================

timeout_produccion = None

for nodo in arbol.body:

    if isinstance(nodo, ast.Assign):

        for objetivo in nodo.targets:

            if (
                isinstance(objetivo, ast.Name)
                and objetivo.id == "TIEMPO_MAX_DECISION"
            ):

                timeout_produccion = ast.literal_eval(
                    nodo.value
                )


if timeout_produccion is None:

    print(
        "FAIL: no se encontro "
        "TIEMPO_MAX_DECISION."
    )

    raise SystemExit(1)


# ============================================================
# LOCALIZAR validar_con_timeout()
# ============================================================

funcion = None

for nodo in ast.walk(arbol):

    if (
        isinstance(nodo, ast.FunctionDef)
        and nodo.name == "validar_con_timeout"
    ):

        funcion = nodo
        break


if funcion is None:

    print(
        "FAIL: no se encontro "
        "validar_con_timeout()."
    )

    raise SystemExit(1)


texto_funcion = (
    ast.get_source_segment(
        codigo,
        funcion
    )
    or ""
)


usa_timeout = (
    "future.result" in texto_funcion
    and "TIEMPO_MAX_DECISION" in texto_funcion
    and "TimeoutError" in texto_funcion
)


# ============================================================
# EJECUTAR LA FUNCION REAL EN UN ENTORNO CONTROLADO
# ============================================================

modulo_prueba = ast.Module(
    body=[funcion],
    type_ignores=[]
)

ast.fix_missing_locations(
    modulo_prueba
)


# Usamos un timeout corto exclusivamente para acelerar
# la prueba. La estructura ejecutada es la función real
# tomada de la aplicación.
TIMEOUT_PRUEBA = 0.20
RETARDO_CLASIFICADOR = 0.60


def clasificador_colgado(_identificador):

    time.sleep(
        RETARDO_CLASIFICADOR
    )

    # Incluso si finalmente autorizara,
    # ya debe haber vencido el timeout.
    return True


executor = ThreadPoolExecutor(
    max_workers=1
)

namespace = {
    "executor_validacion": executor,
    "validar_identificador":
        clasificador_colgado,
    "TIEMPO_MAX_DECISION":
        TIMEOUT_PRUEBA,
    "TimeoutError":
        TimeoutError,
}


exec(
    compile(
        modulo_prueba,
        filename=str(APP),
        mode="exec"
    ),
    namespace
)


inicio = time.monotonic()

autorizado, timeout = (
    namespace[
        "validar_con_timeout"
    ](
        "MC001"
    )
)

duracion = (
    time.monotonic()
    - inicio
)


executor.shutdown(
    wait=True,
    cancel_futures=True
)


# ============================================================
# VALIDACIONES
# ============================================================

timeout_definido = (
    isinstance(
        timeout_produccion,
        (int, float)
    )
    and timeout_produccion > 0
)

deniega_por_timeout = (
    autorizado is False
    and timeout is True
)

timeout_ocurre_a_tiempo = (
    duracion >= TIMEOUT_PRUEBA
    and duracion < RETARDO_CLASIFICADOR
)


criterios = [
    (
        "Timeout de produccion definido",
        timeout_definido
    ),
    (
        "La funcion usa future.result(timeout=...)",
        usa_timeout
    ),
    (
        "Clasificador lento produce timeout",
        timeout is True
    ),
    (
        "Timeout niega el acceso",
        autorizado is False
    ),
    (
        "La decision retorna antes que el clasificador",
        timeout_ocurre_a_tiempo
    ),
]


todo_ok = True

lineas = [
    "H2 - TIMEOUT FAIL-SECURE",
    "",
    (
        "Timeout configurado en produccion: "
        f"{timeout_produccion:.1f} s"
    ),
    (
        "Timeout usado para la prueba: "
        f"{TIMEOUT_PRUEBA:.2f} s"
    ),
    (
        "Retardo simulado del clasificador: "
        f"{RETARDO_CLASIFICADOR:.2f} s"
    ),
    (
        "Tiempo real hasta la decision: "
        f"{duracion:.3f} s"
    ),
    "",
]


for nombre, resultado in criterios:

    estado = (
        "PASS"
        if resultado
        else "FAIL"
    )

    lineas.append(
        f"[{estado}] {nombre}"
    )

    if not resultado:
        todo_ok = False


lineas.extend(
    [
        "",
        f"Autorizado: {autorizado}",
        f"Timeout: {timeout}",
        "",
    ]
)


if todo_ok and deniega_por_timeout:

    lineas.append(
        "PASS: ante un clasificador que excede "
        "el tiempo maximo, el sistema niega "
        "el acceso."
    )

else:

    lineas.append(
        "FAIL: la politica fail-secure "
        "no fue demostrada."
    )

    todo_ok = False


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


if not todo_ok:
    raise SystemExit(1)


print()
print("========================================")
print(" TEST H2 TIMEOUT FAIL-SECURE: PASS")
print("========================================")
