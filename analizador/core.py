"""
Modulo central de analisis esteganografico.

La funcion analizar_archivo() es el unico punto de entrada compartido
por la CLI y la GUI. Recibe la ruta del archivo y un callback opcional
para reportar el progreso, y devuelve una lista de diccionarios de resultados.
"""

from datetime import datetime
from typing import Callable, List, Optional

from .herramientas import (
    run_exiftool,
    run_binwalk,
    run_steghide,
    run_stegseek,
    run_zsteg,
    run_pngcheck,
    run_outguess,
)


# Listado ordenado de (nombre, funcion) que se ejecutaran
HERRAMIENTAS = [
    ("exiftool",  run_exiftool),
    ("binwalk",   run_binwalk),
    ("steghide",  run_steghide),
    ("stegseek",  run_stegseek),
    ("zsteg",     run_zsteg),
    ("pngcheck",  run_pngcheck),
    ("outguess",  run_outguess),
]


def analizar_archivo(
    ruta: str,
    callback: Optional[Callable[[str], None]] = None,
    contrasenas: Optional[List[str]] = None,
) -> List[dict]:
    """
    Analiza un archivo con todas las herramientas de esteganografia disponibles.

    Parametros
    ----------
    ruta        : Ruta absoluta o relativa al archivo objetivo.
    callback    : Funcion opcional que recibe un string de progreso.
                  Util para actualizar la GUI o imprimir en la CLI.
    contrasenas : Lista de contrasenas para steghide.
                  - None           -> usa la lista por defecto (CONTRASENAS_COMUNES)
                  - ["mi_pass"]    -> prueba solo esa contrasena
                  - ["a", "b", ..] -> prueba las indicadas en orden

    Retorna
    -------
    Lista de diccionarios de resultado (uno por herramienta).
    Nunca lanza excepciones; los errores se encapsulan en los resultados.
    """

    def notificar(msg: str):
        if callback:
            try:
                callback(msg)
            except Exception:
                pass  # El callback nunca debe romper el analisis

    resultados: List[dict] = []
    total = len(HERRAMIENTAS)

    for i, (nombre, funcion) in enumerate(HERRAMIENTAS, start=1):
        notificar(f"[{i}/{total}] Ejecutando {nombre}...")
        try:
            # steghide acepta un parametro adicional de contrasenas
            if nombre == "steghide":
                resultado = funcion(ruta, contrasenas=contrasenas)
            else:
                resultado = funcion(ruta)
        except Exception as exc:
            # Salvaguarda: si algo falla de forma inesperada, registrarlo
            resultado = {
                "herramienta":    nombre,
                "comando":        "",
                "aplica":         True,
                "disponible":     True,
                "stdout":         "",
                "stderr":         "",
                "codigo_retorno": -99,
                "error":          f"Error inesperado: {exc}",
                "hallazgos":      f"Fallo critico al ejecutar {nombre}: {exc}",
                "timestamp":      datetime.now().isoformat(),
            }
        resultados.append(resultado)
        notificar(f"[{i}/{total}] {nombre} completado.")

    notificar("Analisis finalizado.")
    return resultados
