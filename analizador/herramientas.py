"""
Modulo de herramientas esteganograficas.

Cada funcion publica recibe la ruta del archivo a analizar y devuelve
un diccionario con la siguiente estructura:

    {
        "herramienta"    : str,   # nombre de la herramienta
        "comando"        : str,   # comando ejecutado (representacion legible)
        "aplica"         : bool,  # True si la herramienta aplica al tipo de archivo
        "disponible"     : bool,  # True si la herramienta esta instalada
        "stdout"         : str,   # salida estandar del proceso
        "stderr"         : str,   # salida de error del proceso
        "codigo_retorno" : int,   # codigo de salida (None si no se ejecuto)
        "error"          : str,   # mensaje de error interno (exception, etc.)
        "hallazgos"      : str,   # resumen legible de lo encontrado
        "timestamp"      : str,   # ISO 8601
    }
"""

import subprocess
import os
from datetime import datetime

from .config import (
    CONTRASENAS_COMUNES,
    WORDLIST_PATH,
    TIMEOUT_HERRAMIENTA,
    DIRECTORIO_SALIDA,
)
from .utilidades import herramienta_disponible, obtener_extension


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _ejecutar(comando: list, timeout: int = TIMEOUT_HERRAMIENTA) -> tuple:
    """
    Ejecuta un comando de forma segura con subprocess.
    Devuelve (stdout, stderr, codigo_retorno).
    Nunca lanza excepciones; los errores se devuelven como texto.
    """
    try:
        resultado = subprocess.run(
            comando,
            capture_output=True,
            timeout=timeout,
        )
        # Decodificar con errors='replace' para tolerar herramientas que
        # emiten bytes en Latin-1 u otras codificaciones no-UTF-8
        # (steghide, por ejemplo, usa la locale del sistema).
        stdout = resultado.stdout.decode("utf-8", errors="replace")
        stderr = resultado.stderr.decode("utf-8", errors="replace")
        return stdout, stderr, resultado.returncode
    except subprocess.TimeoutExpired:
        return "", f"Timeout: el comando supero los {timeout} segundos.", -1
    except FileNotFoundError:
        return "", f"Ejecutable no encontrado: {comando[0]}", -2
    except Exception as exc:
        return "", f"Excepcion al ejecutar: {exc}", -3


def _resultado(
    herramienta: str,
    comando,
    aplica: bool,
    disponible: bool,
    stdout: str = "",
    stderr: str = "",
    codigo_retorno=None,
    error: str = None,
    hallazgos: str = "",
) -> dict:
    """Construye el diccionario de resultado estandar."""
    if isinstance(comando, list):
        cmd_str = " ".join(str(c) for c in comando)
    else:
        cmd_str = str(comando) if comando else ""

    return {
        "herramienta": herramienta,
        "comando": cmd_str,
        "aplica": aplica,
        "disponible": disponible,
        "stdout": stdout,
        "stderr": stderr,
        "codigo_retorno": codigo_retorno,
        "error": error,
        "hallazgos": hallazgos,
        "timestamp": datetime.now().isoformat(),
    }


def _asegurar_directorio_salida():
    """Crea el directorio de salida si no existe."""
    os.makedirs(DIRECTORIO_SALIDA, exist_ok=True)


# ---------------------------------------------------------------------------
# exiftool
# ---------------------------------------------------------------------------

def run_exiftool(ruta: str) -> dict:
    """Extrae todos los metadatos del archivo con exiftool."""
    herramienta = "exiftool"

    if not herramienta_disponible(herramienta):
        return _resultado(
            herramienta, [], True, False,
            error="exiftool no esta instalado.",
            hallazgos="Instala con: sudo apt install libimage-exiftool-perl",
        )

    comando = ["exiftool", ruta]
    stdout, stderr, codigo = _ejecutar(comando)

    hallazgos = "Error al leer metadatos."
    if codigo == 0 and stdout.strip():
        campos = [l for l in stdout.strip().splitlines() if ":" in l]
        hallazgos = f"Se extrajeron {len(campos)} campos de metadatos."
        claves_interes = ["comment", "software", "creator", "artist",
                          "description", "author", "copyright", "warning"]
        relevantes = [
            l for l in campos
            if any(k in l.lower() for k in claves_interes)
        ]
        if relevantes:
            hallazgos += f" Campos de interes encontrados: {len(relevantes)}."
    elif codigo == 0:
        hallazgos = "Sin metadatos detectados."

    return _resultado(herramienta, comando, True, True,
                      stdout=stdout, stderr=stderr,
                      codigo_retorno=codigo, hallazgos=hallazgos)


# ---------------------------------------------------------------------------
# binwalk
# ---------------------------------------------------------------------------

def run_binwalk(ruta: str) -> dict:
    """Escanea firmas para detectar archivos embebidos o codigo ejecutable."""
    herramienta = "binwalk"

    if not herramienta_disponible(herramienta):
        return _resultado(
            herramienta, [], True, False,
            error="binwalk no esta instalado.",
            hallazgos="Instala con: sudo apt install binwalk",
        )

    comando = ["binwalk", ruta]
    stdout, stderr, codigo = _ejecutar(comando)

    hallazgos = "Sin firmas relevantes detectadas."
    if stdout:
        lineas_datos = [
            l for l in stdout.strip().splitlines()
            if l.strip()
            and not l.startswith("DECIMAL")
            and not l.startswith("-")
            and not l.startswith("WARNING")
        ]
        if lineas_datos:
            hallazgos = f"Se detectaron {len(lineas_datos)} firma(s) en el archivo."
            tipos = set()
            for l in lineas_datos:
                for t in ["JPEG", "PNG", "ZIP", "RAR", "ELF", "PDF", "GIF",
                          "BMP", "MP3", "GZIP", "TAR", "7-ZIP"]:
                    if t in l.upper():
                        tipos.add(t)
            if tipos:
                hallazgos += f" Tipos detectados: {', '.join(sorted(tipos))}."

    return _resultado(herramienta, comando, True, True,
                      stdout=stdout, stderr=stderr,
                      codigo_retorno=codigo, hallazgos=hallazgos)


# ---------------------------------------------------------------------------
# steghide
# ---------------------------------------------------------------------------

def run_steghide(ruta: str, contrasenas: list = None) -> dict:
    """
    Intenta extraer datos con steghide.

    Si se recibe 'contrasenas', usa esa lista (puede ser una sola contrasena).
    Si no, usa la lista CONTRASENAS_COMUNES del modulo de configuracion.
    """
    herramienta = "steghide"
    formatos = [".jpg", ".jpeg", ".bmp", ".wav", ".au"]
    ext = obtener_extension(ruta)
    aplica = ext in formatos

    if not aplica:
        return _resultado(
            herramienta, [], False, True,
            hallazgos=(
                f"steghide no soporta el formato '{ext}'. "
                f"Formatos validos: {', '.join(formatos)}"
            ),
        )

    if not herramienta_disponible(herramienta):
        return _resultado(
            herramienta, [], True, False,
            error="steghide no esta instalado.",
            hallazgos="Instala con: sudo apt install steghide",
        )

    # Usar la lista proporcionada o la lista por defecto del config
    lista_contrasenas = contrasenas if contrasenas is not None else CONTRASENAS_COMUNES

    _asegurar_directorio_salida()
    lineas = []
    hallazgos = "No se encontraron datos ocultos con ninguna contrasena probada."
    exito = False

    for i, contrasena in enumerate(lista_contrasenas):
        archivo_salida = os.path.join(
            DIRECTORIO_SALIDA, f"steghide_{os.getpid()}_{i}.bin"
        )
        comando = [
            "steghide", "extract",
            "-sf", ruta,
            "-p", contrasena,
            "-f",
            "-xf", archivo_salida,
        ]
        stdout, stderr, codigo = _ejecutar(comando)

        etiqueta = f"'{contrasena}'" if contrasena else "'(vacia)'"
        if codigo == 0:
            hallazgos = (
                f"EXITO - Contrasena: {etiqueta}. "
                f"Datos extraidos en: {archivo_salida}"
            )
            lineas.append(f"[EXITO] Contrasena {etiqueta} -> {archivo_salida}")
            exito = True
            break
        else:
            detalle = (stderr or stdout or "sin respuesta").strip()
            lineas.append(f"[FALLO] Contrasena {etiqueta} -> {detalle[:100]}")

    modo = "contrasena personalizada" if contrasenas is not None else "fuerza bruta"
    salida = (
        f"Modo: {modo}\n"
        f"Contrasenas probadas: {len(lineas)}\n\n"
        + "\n".join(lineas)
    )

    return _resultado(
        herramienta,
        f"steghide extract -sf {ruta} -p [CONTRASENA] -f -xf [SALIDA]",
        True, True,
        stdout=salida,
        codigo_retorno=0 if exito else 1,
        hallazgos=hallazgos,
    )


# ---------------------------------------------------------------------------
# stegseek
# ---------------------------------------------------------------------------

def run_stegseek(ruta: str) -> dict:
    """Usa stegseek con una wordlist para romper cifrado compatible con steghide."""
    herramienta = "stegseek"
    formatos = [".jpg", ".jpeg", ".bmp", ".wav", ".au"]
    ext = obtener_extension(ruta)
    aplica = ext in formatos

    if not aplica:
        return _resultado(
            herramienta, [], False, True,
            hallazgos=(
                f"stegseek no soporta el formato '{ext}'. "
                f"Formatos validos: {', '.join(formatos)}"
            ),
        )

    if not herramienta_disponible(herramienta):
        return _resultado(
            herramienta, [], True, False,
            error="stegseek no esta instalado.",
            hallazgos=(
                "Instala desde: https://github.com/RickdeJager/stegseek/releases"
            ),
        )

    if not os.path.exists(WORDLIST_PATH):
        return _resultado(
            herramienta, [], True, True,
            error=f"Wordlist no encontrada: {WORDLIST_PATH}",
            hallazgos=(
                f"Configura WORDLIST_PATH en analizador/config.py. "
                f"Ruta actual: {WORDLIST_PATH}"
            ),
        )

    _asegurar_directorio_salida()
    archivo_salida = os.path.join(DIRECTORIO_SALIDA, f"stegseek_{os.getpid()}.bin")
    comando = ["stegseek", "--crack", ruta, WORDLIST_PATH, archivo_salida]
    stdout, stderr, codigo = _ejecutar(comando)

    salida_completa = stdout + stderr
    hallazgos = "No se encontro contrasena valida con la wordlist proporcionada."
    if codigo == 0 or "Found passphrase" in salida_completa:
        hallazgos = (
            f"EXITO - Contrasena encontrada. "
            f"Archivo extraido en: {archivo_salida}"
        )

    return _resultado(herramienta, comando, True, True,
                      stdout=stdout, stderr=stderr,
                      codigo_retorno=codigo, hallazgos=hallazgos)


# ---------------------------------------------------------------------------
# zsteg
# ---------------------------------------------------------------------------

def run_zsteg(ruta: str) -> dict:
    """Detecta datos ocultos en canales LSB de archivos PNG o BMP."""
    herramienta = "zsteg"
    formatos = [".png", ".bmp"]
    ext = obtener_extension(ruta)
    aplica = ext in formatos

    if not aplica:
        return _resultado(
            herramienta, [], False, True,
            hallazgos=(
                f"zsteg no aplica para '{ext}'. "
                f"Formatos validos: {', '.join(formatos)}"
            ),
        )

    if not herramienta_disponible(herramienta):
        return _resultado(
            herramienta, [], True, False,
            error="zsteg no esta instalado.",
            hallazgos="Instala con: sudo gem install zsteg",
        )

    comando = ["zsteg", "-a", ruta]
    stdout, stderr, codigo = _ejecutar(comando)

    hallazgos = "Sin datos ocultos detectados por zsteg."
    if stdout.strip():
        lineas_interes = [
            l for l in stdout.strip().splitlines()
            if l.strip() and "imagedata" not in l.lower()
        ]
        if lineas_interes:
            hallazgos = (
                f"zsteg encontro {len(lineas_interes)} canal(es) con posibles datos."
            )

    return _resultado(herramienta, comando, True, True,
                      stdout=stdout, stderr=stderr,
                      codigo_retorno=codigo, hallazgos=hallazgos)


# ---------------------------------------------------------------------------
# pngcheck
# ---------------------------------------------------------------------------

def run_pngcheck(ruta: str) -> dict:
    """Verifica integridad de un PNG y detecta chunks sospechosos o anomalias."""
    herramienta = "pngcheck"
    ext = obtener_extension(ruta)
    aplica = ext == ".png"

    if not aplica:
        return _resultado(
            herramienta, [], False, True,
            hallazgos=f"pngcheck solo aplica a archivos PNG (extension actual: '{ext}').",
        )

    if not herramienta_disponible(herramienta):
        return _resultado(
            herramienta, [], True, False,
            error="pngcheck no esta instalado.",
            hallazgos="Instala con: sudo apt install pngcheck",
        )

    comando = ["pngcheck", "-v", ruta]
    stdout, stderr, codigo = _ejecutar(comando)

    salida_total = stdout + stderr
    if codigo == 0:
        hallazgos = "PNG integro. Sin anomalias criticas detectadas."
    else:
        hallazgos = "Se detectaron errores o anomalias en el archivo PNG."

    chunks_interes = ["tEXt", "zTXt", "iTXt", "eXIf", "hIST", "sPLT"]
    encontrados = [c for c in chunks_interes if c in salida_total]
    if encontrados:
        hallazgos += f" Chunks de interes: {', '.join(encontrados)}."

    return _resultado(herramienta, comando, True, True,
                      stdout=stdout, stderr=stderr,
                      codigo_retorno=codigo, hallazgos=hallazgos)


# ---------------------------------------------------------------------------
# outguess
# ---------------------------------------------------------------------------

def run_outguess(ruta: str) -> dict:
    """Intenta extraer datos ocultos con outguess (JPEG)."""
    herramienta = "outguess"
    formatos = [".jpg", ".jpeg"]
    ext = obtener_extension(ruta)
    aplica = ext in formatos

    if not aplica:
        return _resultado(
            herramienta, [], False, True,
            hallazgos=(
                f"outguess no aplica para '{ext}'. "
                f"Formatos validos: {', '.join(formatos)}"
            ),
        )

    if not herramienta_disponible(herramienta):
        return _resultado(
            herramienta, [], True, False,
            error="outguess no esta instalado.",
            hallazgos="Instala con: sudo apt install outguess",
        )

    _asegurar_directorio_salida()
    archivo_salida = os.path.join(DIRECTORIO_SALIDA, f"outguess_{os.getpid()}.bin")
    comando = ["outguess", "-r", ruta, archivo_salida]
    stdout, stderr, codigo = _ejecutar(comando)

    hallazgos = "No se encontraron datos ocultos con outguess."
    if codigo == 0 and os.path.exists(archivo_salida):
        tamano = os.path.getsize(archivo_salida)
        if tamano > 0:
            hallazgos = (
                f"EXITO - outguess extrajo {tamano} bytes. "
                f"Archivo: {archivo_salida}"
            )
        else:
            hallazgos = "outguess extrajo un archivo vacio (sin datos ocultos)."

    return _resultado(herramienta, comando, True, True,
                      stdout=stdout, stderr=stderr,
                      codigo_retorno=codigo, hallazgos=hallazgos)
