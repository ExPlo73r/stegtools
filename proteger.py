#!/usr/bin/env python3
"""
proteger.py - Script de proteccion/ofuscacion de Viernez13 StegTools

Opciones disponibles:
  --pyarmor   Ofuscar con PyArmor (bytecode cifrado, recomendado)
  --nuitka    Compilar a binario nativo con Nuitka (maxima proteccion)
  --pyc       Compilar a .pyc y eliminar fuentes (proteccion basica)
  --limpiar   Eliminar el directorio de salida anterior

Uso:
  python3 proteger.py --pyarmor
  python3 proteger.py --nuitka
  python3 proteger.py --pyc
"""

import argparse
import os
import sys
import shutil
import subprocess
import compileall
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------------

DIRECTORIO_BASE    = Path(__file__).parent.resolve()
DIRECTORIO_DIST    = DIRECTORIO_BASE / "dist"
DIRECTORIO_PYARMOR = DIRECTORIO_DIST / "pyarmor"
DIRECTORIO_NUITKA  = DIRECTORIO_DIST / "nuitka"
DIRECTORIO_PYC     = DIRECTORIO_DIST / "pyc"

# Archivos fuente a proteger
FUENTES_PRINCIPALES = [
    "main.py",
    "gui.py",
]
PAQUETE_ANALIZADOR = "analizador"

# Archivos a copiar sin modificar (datos, recursos)
RECURSOS = [
    "Cybeer.png",
    "requirements.txt",
]


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _run(cmd: list, **kwargs) -> int:
    """Ejecuta un comando y devuelve el codigo de salida."""
    print(f"\n  $ {' '.join(str(c) for c in cmd)}")
    resultado = subprocess.run(cmd, **kwargs)
    return resultado.returncode


def _verificar_herramienta(nombre: str) -> bool:
    """Verifica si una herramienta esta disponible en el PATH."""
    return shutil.which(nombre) is not None


def _copiar_recursos(destino: Path):
    """Copia recursos estaticos al directorio de destino."""
    for recurso in RECURSOS:
        src = DIRECTORIO_BASE / recurso
        if src.exists():
            shutil.copy2(src, destino / recurso)
            print(f"  [+] Recurso copiado: {recurso}")


def _limpiar(directorio: Path):
    """Elimina el directorio indicado."""
    if directorio.exists():
        shutil.rmtree(directorio)
        print(f"  [+] Eliminado: {directorio}")
    else:
        print(f"  [!] No existe: {directorio}")


# ---------------------------------------------------------------------------
# Metodo 1: PyArmor
# ---------------------------------------------------------------------------

def proteger_pyarmor():
    """
    Ofusca el codigo con PyArmor.

    PyArmor cifra el bytecode y lo envuelve en una capa de licencia.
    El codigo resultante no es legible directamente y es muy dificil
    de decompilar.

    Instalacion previa:
        pip install pyarmor
    """
    print("\n" + "=" * 60)
    print("  PROTECCION CON PYARMOR")
    print("=" * 60)

    if not _verificar_herramienta("pyarmor"):
        print("\n  [ERROR] PyArmor no esta instalado.")
        print("  Instala con: pip install pyarmor")
        sys.exit(1)

    DIRECTORIO_PYARMOR.mkdir(parents=True, exist_ok=True)

    # Generar version ofuscada de todos los fuentes
    archivos = [str(DIRECTORIO_BASE / f) for f in FUENTES_PRINCIPALES]
    paquete  = str(DIRECTORIO_BASE / PAQUETE_ANALIZADOR)

    codigo = _run([
        "pyarmor", "gen",
        "--output", str(DIRECTORIO_PYARMOR),
        "--recursive",          # incluir subdirectorios
        *archivos,
        paquete,
    ])

    if codigo != 0:
        print("\n  [ERROR] PyArmor termino con errores.")
        sys.exit(1)

    _copiar_recursos(DIRECTORIO_PYARMOR)

    print(f"\n  [OK] Codigo ofuscado generado en: {DIRECTORIO_PYARMOR}")
    print("  Para ejecutar: cd dist/pyarmor && python3 main.py")
    print("  Para la GUI  : cd dist/pyarmor && python3 main.py --gui")


# ---------------------------------------------------------------------------
# Metodo 2: Nuitka (compilacion a binario nativo)
# ---------------------------------------------------------------------------

def proteger_nuitka():
    """
    Compila el proyecto a un binario nativo con Nuitka.

    Nuitka convierte Python a C y luego compila a un ejecutable.
    Es la proteccion mas fuerte: no hay codigo Python visible,
    no hay bytecode decompilable, solo un binario nativo.

    Instalacion previa:
        pip install nuitka
        sudo apt install patchelf  (en Linux)
    """
    print("\n" + "=" * 60)
    print("  COMPILACION CON NUITKA (binario nativo)")
    print("=" * 60)

    if not _verificar_herramienta("nuitka"):
        print("\n  [ERROR] Nuitka no esta instalado.")
        print("  Instala con: pip install nuitka")
        sys.exit(1)

    DIRECTORIO_NUITKA.mkdir(parents=True, exist_ok=True)

    codigo = _run([
        sys.executable, "-m", "nuitka",
        "--standalone",             # incluir todo en un directorio portatil
        "--onefile",                # un solo ejecutable
        "--output-dir=" + str(DIRECTORIO_NUITKA),
        "--output-filename=stegtools",
        "--follow-imports",
        "--include-package=analizador",
        "--include-data-files=" + str(DIRECTORIO_BASE / "Cybeer.png") + "=Cybeer.png",
        "--nofollow-import-to=tkinter",   # usar el tkinter del sistema
        "--enable-plugin=tk-inter",        # soporte GUI
        "--remove-output",          # limpiar archivos intermedios C
        str(DIRECTORIO_BASE / "main.py"),
    ])

    if codigo != 0:
        print("\n  [ERROR] Nuitka termino con errores.")
        sys.exit(1)

    _copiar_recursos(DIRECTORIO_NUITKA)

    ejecutable = DIRECTORIO_NUITKA / "stegtools"
    if ejecutable.exists():
        ejecutable.chmod(0o755)

    print(f"\n  [OK] Binario generado en: {DIRECTORIO_NUITKA}/stegtools")
    print("  Para ejecutar la CLI: ./dist/nuitka/stegtools imagen.jpg")
    print("  Para la GUI        : ./dist/nuitka/stegtools --gui")


# ---------------------------------------------------------------------------
# Metodo 3: Compilar a .pyc (proteccion basica)
# ---------------------------------------------------------------------------

def proteger_pyc():
    """
    Compila todos los fuentes a bytecode .pyc y elimina los .py originales
    del directorio de distribucion.

    ADVERTENCIA: Esta proteccion es BASICA. Herramientas como uncompyle6
    o decompile3 pueden recuperar el codigo fuente desde .pyc con relativa
    facilidad. Usar solo como primera capa de proteccion.
    """
    print("\n" + "=" * 60)
    print("  COMPILACION A .pyc (proteccion basica)")
    print("=" * 60)

    if DIRECTORIO_PYC.exists():
        shutil.rmtree(DIRECTORIO_PYC)

    # Copiar todo el proyecto al directorio de salida
    shutil.copytree(
        DIRECTORIO_BASE,
        DIRECTORIO_PYC,
        ignore=shutil.ignore_patterns(
            "__pycache__", "*.pyc", "dist", ".git",
            "proteger.py",          # no incluir este script
        ),
    )

    print(f"  [+] Proyecto copiado en: {DIRECTORIO_PYC}")

    # Compilar a bytecode
    print("  [+] Compilando fuentes a .pyc ...")
    compileall.compile_dir(
        str(DIRECTORIO_PYC),
        force=True,
        quiet=1,
        optimize=2,   # -OO: elimina docstrings y asserts
    )

    # Eliminar archivos .py del directorio de distribucion
    eliminados = 0
    for py_file in DIRECTORIO_PYC.rglob("*.py"):
        py_file.unlink()
        eliminados += 1

    print(f"  [+] {eliminados} archivos .py eliminados del directorio de salida.")
    print(f"\n  [OK] Distribucion con .pyc en: {DIRECTORIO_PYC}")
    print("  NOTA: Proteccion basica. Usa PyArmor o Nuitka para mayor seguridad.")


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Protege/ofusca Viernez13 StegTools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Niveles de proteccion (de menor a mayor):
  --pyc      Bytecode .pyc  (basico, decompilable con herramientas publicas)
  --pyarmor  PyArmor        (bueno, bytecode cifrado con licencia)
  --nuitka   Nuitka         (maximo, compila a binario nativo C)
        """,
    )
    parser.add_argument("--pyarmor",  action="store_true",
                        help="Ofuscar con PyArmor (recomendado)")
    parser.add_argument("--nuitka",   action="store_true",
                        help="Compilar a binario nativo con Nuitka")
    parser.add_argument("--pyc",      action="store_true",
                        help="Compilar a .pyc y eliminar fuentes (basico)")
    parser.add_argument("--limpiar",  action="store_true",
                        help="Eliminar directorio dist/ completo")

    args = parser.parse_args()

    if args.limpiar:
        _limpiar(DIRECTORIO_DIST)
        return

    if not any([args.pyarmor, args.nuitka, args.pyc]):
        parser.print_help()
        sys.exit(0)

    print("\n" + "=" * 60)
    print("  Viernez13 StegTools - Script de Proteccion")
    print("=" * 60)
    print(f"  Directorio base : {DIRECTORIO_BASE}")
    print(f"  Directorio dist : {DIRECTORIO_DIST}")

    if args.pyarmor:
        proteger_pyarmor()
    elif args.nuitka:
        proteger_nuitka()
    elif args.pyc:
        proteger_pyc()


if __name__ == "__main__":
    main()
