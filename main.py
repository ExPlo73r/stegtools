#!/usr/bin/env python3
"""
Viernez13 StegTools - Punto de entrada principal.

Uso como CLI:
    python main.py <archivo>
    python main.py imagen.jpg --salida reporte.txt --json reporte.json
    python main.py imagen.jpg --wordlist /ruta/a/rockyou.txt

Uso para abrir la GUI:
    python main.py --gui
    python main.py -g
"""

import argparse
import sys
import os


def _construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="steganalisis",
        description="Viernez13 StegTools - Analisis esteganografico multi-herramienta",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python main.py foto.jpg
  python main.py foto.jpg -o reporte.txt -j reporte.json
  python main.py foto.png --wordlist /usr/share/wordlists/rockyou.txt
  python main.py --gui
        """,
    )
    parser.add_argument(
        "archivo",
        nargs="?",
        help="Ruta al archivo que se desea analizar.",
    )
    parser.add_argument(
        "--gui", "-g",
        action="store_true",
        help="Lanzar la interfaz grafica (GUI).",
    )
    parser.add_argument(
        "--salida", "-o",
        metavar="ARCHIVO_TXT",
        help="Guardar el reporte completo en un archivo de texto.",
    )
    parser.add_argument(
        "--json", "-j",
        metavar="ARCHIVO_JSON",
        help="Guardar el reporte completo en formato JSON.",
    )
    parser.add_argument(
        "--wordlist", "-w",
        metavar="RUTA",
        help="Ruta alternativa a la wordlist para stegseek.",
    )
    return parser


def _ejecutar_cli(args):
    """Modo linea de comandos."""
    # Importaciones diferidas para no ralentizar el inicio de la GUI
    from analizador.core import analizar_archivo
    from analizador.utilidades import (
        formatear_resultado_texto,
        formatear_resumen,
        guardar_reporte_txt,
        guardar_reporte_json,
    )

    ruta = args.archivo

    if not os.path.exists(ruta):
        print(f"\n[ERROR] El archivo no existe: {ruta}", file=sys.stderr)
        sys.exit(1)

    # Sobreescribir wordlist si el usuario la proporciono
    if args.wordlist:
        from analizador import config
        config.WORDLIST_PATH = args.wordlist
        print(f"[INFO] Usando wordlist: {args.wordlist}")

    # Encabezado
    print()
    print("=" * 72)
    print("  Viernez13 StegTools - Analisis Esteganografico")
    print("=" * 72)
    print(f"  Archivo  : {os.path.abspath(ruta)}")
    print(f"  Tamano   : {os.path.getsize(ruta):,} bytes")
    print("=" * 72)
    print()

    def progreso(msg: str):
        print(f"  >> {msg}")

    # Ejecutar analisis
    resultados = analizar_archivo(ruta, callback=progreso)

    print()

    # Mostrar resultados por herramienta
    for resultado in resultados:
        print(formatear_resultado_texto(resultado))

    # Mostrar resumen final
    print(formatear_resumen(resultados))
    print()

    # Guardar reportes si se solicitaron
    if args.salida:
        try:
            guardar_reporte_txt(resultados, args.salida)
            print(f"[+] Reporte TXT guardado en: {args.salida}")
        except Exception as exc:
            print(f"[ERROR] No se pudo guardar el TXT: {exc}", file=sys.stderr)

    if args.json:
        try:
            guardar_reporte_json(resultados, args.json)
            print(f"[+] Reporte JSON guardado en: {args.json}")
        except Exception as exc:
            print(f"[ERROR] No se pudo guardar el JSON: {exc}", file=sys.stderr)


def main():
    parser = _construir_parser()
    args = parser.parse_args()

    if args.gui:
        # Lanzar interfaz grafica
        try:
            from gui import lanzar_gui
            lanzar_gui()
        except ImportError as exc:
            print(f"[ERROR] No se pudo cargar la GUI: {exc}", file=sys.stderr)
            sys.exit(1)
        return

    if not args.archivo:
        parser.print_help()
        sys.exit(0)

    _ejecutar_cli(args)


if __name__ == "__main__":
    main()
