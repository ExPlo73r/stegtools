"""
Funciones de utilidad compartidas entre CLI y GUI:
  - Verificar disponibilidad de herramientas
  - Obtener extension de archivo
  - Formatear resultados como texto legible
  - Guardar reportes en TXT y JSON
"""

import shutil
import json
import os
from datetime import datetime


# ---------------------------------------------------------------------------
# Deteccion de herramientas
# ---------------------------------------------------------------------------

def herramienta_disponible(nombre: str) -> bool:
    """Devuelve True si la herramienta esta instalada y accesible en el PATH."""
    return shutil.which(nombre) is not None


# ---------------------------------------------------------------------------
# Inspeccion de archivos
# ---------------------------------------------------------------------------

def obtener_extension(ruta: str) -> str:
    """Devuelve la extension del archivo en minusculas (incluyendo el punto)."""
    _, ext = os.path.splitext(ruta)
    return ext.lower()


# ---------------------------------------------------------------------------
# Formateo de resultados para salida en texto
# ---------------------------------------------------------------------------

def formatear_resultado_texto(resultado: dict) -> str:
    """
    Convierte un diccionario de resultado en un bloque de texto
    con encabezados claros, listo para imprimir o guardar.
    """
    SEP = "=" * 72
    SEP_M = "-" * 72
    lineas = []

    herramienta = resultado.get("herramienta", "desconocida").upper()
    lineas.append(SEP)
    lineas.append(f"  HERRAMIENTA: {herramienta}")
    lineas.append(SEP)

    # Caso: no aplica al tipo de archivo
    if not resultado.get("aplica", True):
        lineas.append(f"  [NO APLICA]  {resultado.get('hallazgos', '')}")
        lineas.append("")
        return "\n".join(lineas)

    # Caso: herramienta no instalada
    if not resultado.get("disponible", True):
        lineas.append(f"  [NO DISPONIBLE]  {resultado.get('error', '')}")
        lineas.append(f"  Sugerencia: {resultado.get('hallazgos', '')}")
        lineas.append("")
        return "\n".join(lineas)

    # Informacion de ejecucion
    if resultado.get("comando"):
        lineas.append(f"  Comando    : {resultado['comando']}")
    lineas.append(f"  Retorno    : {resultado.get('codigo_retorno', 'N/A')}")
    lineas.append(f"  Timestamp  : {resultado.get('timestamp', '')}")
    lineas.append(SEP_M)

    if resultado.get("stdout"):
        lineas.append("  [SALIDA ESTANDAR]")
        lineas.append(resultado["stdout"].rstrip())
        lineas.append("")

    if resultado.get("stderr"):
        lineas.append("  [STDERR / ADVERTENCIAS]")
        lineas.append(resultado["stderr"].rstrip())
        lineas.append("")

    if resultado.get("error"):
        lineas.append(f"  [ERROR INTERNO] {resultado['error']}")
        lineas.append("")

    lineas.append(SEP_M)
    lineas.append(f"  HALLAZGOS: {resultado.get('hallazgos', 'Sin informacion.')}")
    lineas.append("")
    return "\n".join(lineas)


def formatear_resumen(resultados: list) -> str:
    """Genera un bloque de resumen con el estado de todas las herramientas."""
    SEP = "=" * 72
    lineas = [SEP, "  RESUMEN FINAL", SEP]

    for r in resultados:
        herramienta = r.get("herramienta", "?")
        if not r.get("aplica", True):
            estado = "NO APLICA   "
        elif not r.get("disponible", True):
            estado = "NO INSTALADA"
        elif r.get("error") and r.get("codigo_retorno", 0) not in (0, 1):
            estado = "ERROR       "
        elif r.get("codigo_retorno", -1) == 0:
            estado = "OK          "
        else:
            estado = "EJECUTADO   "

        hallazgo = r.get("hallazgos", "")[:65]
        lineas.append(f"  [{estado}] {herramienta:<12}  {hallazgo}")

    lineas.append(SEP)
    return "\n".join(lineas)


# ---------------------------------------------------------------------------
# Exportacion de reportes
# ---------------------------------------------------------------------------

def guardar_reporte_txt(resultados: list, ruta_salida: str) -> None:
    """Guarda el reporte completo en formato texto plano."""
    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write("REPORTE DE ANALISIS ESTEGANOGRAFICO - Viernez13 StegTools\n")
        f.write(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 72 + "\n\n")
        for r in resultados:
            f.write(formatear_resultado_texto(r))
            f.write("\n")
        f.write(formatear_resumen(resultados))
        f.write("\n")


def guardar_reporte_json(resultados: list, ruta_salida: str) -> None:
    """Guarda el reporte completo en formato JSON."""
    reporte = {
        "aplicacion": "Viernez13 StegTools",
        "timestamp": datetime.now().isoformat(),
        "total_herramientas": len(resultados),
        "resultados": resultados,
    }
    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(reporte, f, ensure_ascii=False, indent=2)
