#!/usr/bin/env python3
"""
Interfaz grafica (GUI) para Viernez13 StegTools.

Tema visual: Windows XP Silver (colores plateados/grises clasicos).
El analisis se ejecuta en un hilo separado para no bloquear la interfaz.
La comunicacion hilo->GUI se realiza mediante queue.Queue + root.after().
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import queue
import os
import webbrowser
from datetime import datetime
from typing import Optional, List

from analizador.core import analizar_archivo
from analizador.utilidades import guardar_reporte_txt, guardar_reporte_json
from analizador import config

# ---------------------------------------------------------------------------
# Soporte opcional de Pillow para mejor escalado de imagenes
# ---------------------------------------------------------------------------
try:
    from PIL import Image, ImageTk
    _PILLOW = True
except ImportError:
    _PILLOW = False


# ---------------------------------------------------------------------------
# Paleta de colores - Tema Windows XP Silver
# ---------------------------------------------------------------------------
C = {
    # Fondos principales
    "fondo":        "#ECE9D8",   # fondo clasico XP
    "fondo_panel":  "#D4D0C8",   # panel/grupo plateado
    "fondo_entry":  "#FFFFFF",   # campos de texto
    "fondo_salida": "#0D1117",   # area de salida (oscura para legibilidad)

    # Barra de titulo XP
    "xp_barra":     "#1C4897",   # azul oscuro XP
    "xp_barra2":    "#3A6BC0",   # azul claro XP (acento)

    # Texto
    "texto":        "#000000",
    "texto_gris":   "#444444",
    "texto_tenue":  "#777777",
    "texto_claro":  "#E0E0E0",   # para fondos oscuros

    # Estado / alertas
    "rojo":         "#CC0000",   # titulo rojo Viernez13
    "verde":        "#006400",
    "naranja":      "#CC5500",
    "azul":         "#1C4897",
    "azul_claro":   "#316AC5",

    # Botones XP
    "btn":          "#D4D0C8",
    "btn_hover":    "#B8B5AC",
    "btn_analizar": "#CC0000",
    "btn_anal_h":   "#EE1111",

    # Bordes
    "borde":        "#808080",
    "borde_claro":  "#ACA899",

    # Tags de salida (sobre fondo oscuro)
    "tag_titulo":   "#FF4444",
    "tag_label":    "#F0C040",
    "tag_ok":       "#44CC44",
    "tag_err":      "#FF6633",
    "tag_azul":     "#66AAFF",
    "tag_sep":      "#2A2A3A",
    "tag_sep2":     "#3A3A5A",
}

URL_CYBEERSECURITY = "https://www.cybeersecurity.cl"
RUTA_IMAGEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Cybeer.png")


# ---------------------------------------------------------------------------
# Utilidad: cargar imagen con escalado
# ---------------------------------------------------------------------------

def _cargar_imagen(ruta: str, ancho_max: int, alto_max: int):
    """
    Carga una imagen PNG y la escala al tamano indicado.
    Usa Pillow si esta disponible; si no, usa tk.PhotoImage con subsample.
    Devuelve un objeto PhotoImage o None si falla.
    """
    if not os.path.exists(ruta):
        return None
    try:
        if _PILLOW:
            img = Image.open(ruta).convert("RGBA")
            img.thumbnail((ancho_max, alto_max), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        else:
            img = tk.PhotoImage(file=ruta)
            w, h = img.width(), img.height()
            factor = max(1, max(w // ancho_max, h // alto_max))
            if factor > 1:
                img = img.subsample(factor, factor)
            return img
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Ventana principal
# ---------------------------------------------------------------------------

class AplicacionSteg(tk.Tk):
    """Ventana principal de Viernez13 StegTools - tema XP Silver."""

    def __init__(self):
        super().__init__()

        self.title("Viernez13 StegTools - Analisis Esteganografico")
        self.geometry("1150x790")
        self.minsize(960, 660)
        self.configure(bg=C["fondo"])

        # Referencias a imagenes (evitar garbage collection)
        self._img_header: Optional[object] = None
        self._img_about:  Optional[object] = None

        # Estado interno
        self._cola: queue.Queue = queue.Queue()
        self._hilo: Optional[threading.Thread] = None
        self._resultados: List[dict] = []

        self._construir_ui()
        self._iniciar_polling()

    # -----------------------------------------------------------------------
    # Construccion de la interfaz
    # -----------------------------------------------------------------------

    def _construir_ui(self):
        self._crear_barra_titulo_xp()
        self._crear_encabezado()
        self._crear_separador()
        self._crear_panel_controles()
        self._crear_barra_botones()
        self._crear_barra_estado()
        self._crear_separador()
        self._crear_notebook()

    def _crear_barra_titulo_xp(self):
        """Franja azul estrecha en la parte superior (decorativa, estilo XP)."""
        barra = tk.Frame(self, bg=C["xp_barra"], height=5)
        barra.pack(fill=tk.X)
        barra.pack_propagate(False)

    def _crear_encabezado(self):
        """
        Header con dos columnas:
          Izquierda : titulo 'Viernez13 Stegtools' en rojo + subtitulo
          Derecha   : imagen Cybeer.png + 'Cybersecurity Rules!'
        """
        frame = tk.Frame(self, bg=C["fondo"], pady=12)
        frame.pack(fill=tk.X, padx=10)

        # --- Columna izquierda: titulo ---
        col_izq = tk.Frame(frame, bg=C["fondo"])
        col_izq.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(6, 0))

        # Linea decorativa azul debajo del titulo
        tk.Label(
            col_izq,
            text="Viernez13 Stegtools",
            font=("Tahoma", 30, "bold"),
            fg=C["rojo"],
            bg=C["fondo"],
            anchor="w",
        ).pack(anchor="w")

        tk.Label(
            col_izq,
            text="Herramienta de Analisis Esteganografico Multi-Motor",
            font=("Tahoma", 11),
            fg=C["texto_gris"],
            bg=C["fondo"],
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        tk.Label(
            col_izq,
            text="exiftool  |  binwalk  |  steghide  |  stegseek  |  zsteg  |  pngcheck  |  outguess",
            font=("Tahoma", 9),
            fg=C["texto_tenue"],
            bg=C["fondo"],
            anchor="w",
        ).pack(anchor="w", pady=(4, 0))

        # --- Columna derecha: imagen + texto ---
        col_der = tk.Frame(frame, bg=C["fondo"])
        col_der.pack(side=tk.RIGHT, padx=(0, 10))

        self._img_header = _cargar_imagen(RUTA_IMAGEN, ancho_max=110, alto_max=90)
        if self._img_header:
            tk.Label(
                col_der,
                image=self._img_header,
                bg=C["fondo"],
                relief=tk.FLAT,
            ).pack()
        else:
            # Placeholder si la imagen no existe
            tk.Label(
                col_der,
                text="[ Cybeer.png ]",
                font=("Tahoma", 9),
                fg=C["texto_tenue"],
                bg=C["fondo_panel"],
                relief=tk.GROOVE,
                padx=18, pady=18,
            ).pack()

        tk.Label(
            col_der,
            text="Cybersecurity Rules!",
            font=("Tahoma", 10, "bold"),
            fg=C["azul"],
            bg=C["fondo"],
        ).pack(pady=(4, 0))

    def _crear_separador(self):
        sep = tk.Frame(self, bg=C["borde"], height=1)
        sep.pack(fill=tk.X, padx=6, pady=2)

    def _crear_panel_controles(self):
        """Panel con seleccion de archivo, wordlist, password y modo."""
        # Marco con borde estilo XP
        marco = tk.LabelFrame(
            self,
            text=" Configuracion del analisis ",
            font=("Tahoma", 9, "bold"),
            bg=C["fondo"],
            fg=C["texto_gris"],
            relief=tk.GROOVE,
            bd=2,
            padx=10, pady=6,
        )
        marco.pack(fill=tk.X, padx=10, pady=(4, 2))

        lbl_kwargs = dict(bg=C["fondo"], fg=C["texto"], font=("Tahoma", 9, "bold"),
                          width=12, anchor="w")
        entry_kwargs = dict(bg=C["fondo_entry"], fg=C["texto"], relief=tk.SUNKEN,
                            font=("Courier", 10), bd=2)
        btn_kwargs = dict(bg=C["btn"], fg=C["texto"], relief=tk.RAISED,
                          font=("Tahoma", 9), padx=8, cursor="hand2",
                          activebackground=C["btn_hover"])

        # --- Fila 0: Archivo ---
        tk.Label(marco, text="Archivo:", **lbl_kwargs).grid(
            row=0, column=0, padx=(0, 4), pady=3, sticky="w")

        self.var_archivo = tk.StringVar()
        tk.Entry(marco, textvariable=self.var_archivo, **entry_kwargs).grid(
            row=0, column=1, padx=4, pady=3, sticky="ew")

        tk.Button(marco, text="Examinar...",
                  command=self._seleccionar_archivo, **btn_kwargs).grid(
            row=0, column=2, padx=(4, 0), pady=3)

        # --- Fila 1: Wordlist ---
        tk.Label(marco, text="Wordlist:", **lbl_kwargs).grid(
            row=1, column=0, padx=(0, 4), pady=3, sticky="w")

        self.var_wordlist = tk.StringVar(value=config.WORDLIST_PATH)
        tk.Entry(marco, textvariable=self.var_wordlist, **entry_kwargs).grid(
            row=1, column=1, padx=4, pady=3, sticky="ew")

        tk.Button(marco, text="Examinar...",
                  command=self._seleccionar_wordlist, **btn_kwargs).grid(
            row=1, column=2, padx=(4, 0), pady=3)

        # --- Fila 2: Password + checkbox fuerza bruta ---
        tk.Label(marco, text="Password:", **lbl_kwargs).grid(
            row=2, column=0, padx=(0, 4), pady=3, sticky="w")

        frame_pwd = tk.Frame(marco, bg=C["fondo"])
        frame_pwd.grid(row=2, column=1, padx=4, pady=3, sticky="ew")

        self.var_password = tk.StringVar()
        self.entry_password = tk.Entry(
            frame_pwd,
            textvariable=self.var_password,
            show="*",           # ocultar caracteres
            **entry_kwargs,
        )
        self.entry_password.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Boton para mostrar/ocultar contrasena
        self.var_mostrar_pwd = tk.BooleanVar(value=False)
        tk.Checkbutton(
            frame_pwd,
            text="Mostrar",
            variable=self.var_mostrar_pwd,
            command=self._toggle_mostrar_pwd,
            bg=C["fondo"], fg=C["texto_gris"],
            font=("Tahoma", 8),
            relief=tk.FLAT,
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=(6, 0))

        # Checkbox: Fuerza bruta
        self.var_fuerza_bruta = tk.BooleanVar(value=True)
        self.chk_fb = tk.Checkbutton(
            marco,
            text="Usar fuerza bruta (ignorar password)",
            variable=self.var_fuerza_bruta,
            command=self._toggle_fuerza_bruta,
            bg=C["fondo"], fg=C["texto_gris"],
            font=("Tahoma", 9),
            relief=tk.FLAT,
            cursor="hand2",
            selectcolor=C["fondo_entry"],
        )
        self.chk_fb.grid(row=2, column=2, padx=(4, 0), pady=3, sticky="w")

        marco.columnconfigure(1, weight=1)

        # Estado inicial: fuerza bruta activa -> entry deshabilitado
        self._toggle_fuerza_bruta()

    def _crear_barra_botones(self):
        """Fila de botones de accion."""
        frame = tk.Frame(self, bg=C["fondo_panel"], padx=10, pady=6,
                         relief=tk.GROOVE, bd=1)
        frame.pack(fill=tk.X, padx=10, pady=(2, 2))

        btn_base = dict(relief=tk.RAISED, font=("Tahoma", 10, "bold"),
                        padx=14, pady=6, cursor="hand2", bd=2)

        self.btn_analizar = tk.Button(
            frame, text="  ANALIZAR  ",
            command=self._iniciar_analisis,
            bg=C["btn_analizar"], fg="white",
            activebackground=C["btn_anal_h"], activeforeground="white",
            **btn_base,
        )
        self.btn_analizar.pack(side=tk.LEFT, padx=(0, 6))

        btn_sec = dict(bg=C["btn"], fg=C["texto"],
                       activebackground=C["btn_hover"],
                       relief=tk.RAISED, font=("Tahoma", 9),
                       padx=10, pady=6, cursor="hand2", bd=2)

        self.btn_txt = tk.Button(
            frame, text="Exportar TXT",
            command=self._exportar_txt,
            state=tk.DISABLED, **btn_sec)
        self.btn_txt.pack(side=tk.LEFT, padx=4)

        self.btn_json = tk.Button(
            frame, text="Exportar JSON",
            command=self._exportar_json,
            state=tk.DISABLED, **btn_sec)
        self.btn_json.pack(side=tk.LEFT, padx=4)

        tk.Button(frame, text="Limpiar",
                  command=self._limpiar_todo, **btn_sec).pack(
            side=tk.LEFT, padx=4)

        # --- Boton Acerca de (derecha) ---
        tk.Button(
            frame, text="Acerca de...",
            command=self._ventana_acerca_de,
            bg=C["btn"], fg=C["azul"],
            activebackground=C["btn_hover"],
            relief=tk.RAISED, font=("Tahoma", 9, "bold"),
            padx=10, pady=6, cursor="hand2", bd=2,
        ).pack(side=tk.RIGHT, padx=(4, 0))

    def _crear_barra_estado(self):
        """Etiqueta de estado con borde sunken (estilo XP statusbar)."""
        frame = tk.Frame(self, bg=C["fondo_panel"], relief=tk.SUNKEN, bd=1)
        frame.pack(fill=tk.X, padx=10, pady=(2, 2))

        self.var_estado = tk.StringVar(
            value="Listo. Selecciona un archivo y pulsa ANALIZAR.")
        self.lbl_estado = tk.Label(
            frame,
            textvariable=self.var_estado,
            bg=C["fondo_panel"], fg=C["verde"],
            font=("Tahoma", 9), anchor="w", padx=8, pady=3,
        )
        self.lbl_estado.pack(fill=tk.X)

    def _crear_notebook(self):
        """Notebook con pestanas por herramienta - estilo XP."""
        estilo = ttk.Style(self)
        estilo.theme_use("clam")

        estilo.configure("TNotebook",
                         background=C["fondo"],
                         borderwidth=1,
                         tabmargins=[2, 5, 2, 0])
        estilo.configure("TNotebook.Tab",
                         background=C["fondo_panel"],
                         foreground=C["texto_gris"],
                         padding=[10, 4],
                         font=("Tahoma", 9))
        estilo.map("TNotebook.Tab",
                   background=[("selected", C["fondo_entry"])],
                   foreground=[("selected", C["texto"])],
                   expand=[("selected", [1, 1, 1, 0])])

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))

        self._mostrar_tab_bienvenida()

    # -----------------------------------------------------------------------
    # Logica de la password y fuerza bruta
    # -----------------------------------------------------------------------

    def _toggle_fuerza_bruta(self):
        """Habilita o deshabilita el campo de password segun el checkbox."""
        if self.var_fuerza_bruta.get():
            # Fuerza bruta activa: deshabilitar entry de password
            self.entry_password.configure(state=tk.DISABLED, bg="#E0E0E0")
        else:
            # Fuerza bruta desactiva: habilitar entry de password
            self.entry_password.configure(state=tk.NORMAL, bg=C["fondo_entry"])

    def _toggle_mostrar_pwd(self):
        """Alterna mostrar u ocultar la contrasena en el campo."""
        if self.var_mostrar_pwd.get():
            self.entry_password.configure(show="")
        else:
            self.entry_password.configure(show="*")

    def _obtener_contrasenas(self) -> Optional[List[str]]:
        """
        Devuelve la lista de contrasenas a usar para steghide:
          - None         si fuerza bruta esta activa (usa CONTRASENAS_COMUNES)
          - ["pwd"]      si se especifico una contrasena concreta
        """
        if self.var_fuerza_bruta.get():
            return None  # el modulo usara CONTRASENAS_COMUNES
        pwd = self.var_password.get()
        return [pwd]     # puede ser cadena vacia (contrasena vacia)

    # -----------------------------------------------------------------------
    # Tabs de contenido
    # -----------------------------------------------------------------------

    def _texto_con_scroll(self, parent) -> tk.Text:
        """Crea un widget Text oscuro con scrollbars (para salida de herramientas)."""
        frame = tk.Frame(parent, bg=C["fondo"])
        frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        sb_v = tk.Scrollbar(frame, orient=tk.VERTICAL, bg=C["fondo_panel"])
        sb_h = tk.Scrollbar(frame, orient=tk.HORIZONTAL, bg=C["fondo_panel"])

        widget = tk.Text(
            frame,
            wrap=tk.NONE,
            bg=C["fondo_salida"],
            fg=C["texto_claro"],
            font=("Courier New", 10),
            insertbackground=C["texto_claro"],
            selectbackground=C["azul_claro"],
            relief=tk.SUNKEN, bd=2,
            yscrollcommand=sb_v.set,
            xscrollcommand=sb_h.set,
        )

        sb_v.config(command=widget.yview)
        sb_h.config(command=widget.xview)

        sb_v.pack(side=tk.RIGHT, fill=tk.Y)
        sb_h.pack(side=tk.BOTTOM, fill=tk.X)
        widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        return widget

    def _aplicar_tags(self, w: tk.Text):
        """Registra todos los tags de color para el widget de salida."""
        w.tag_configure("titulo",    foreground=C["tag_titulo"],
                                     font=("Courier New", 12, "bold"))
        w.tag_configure("subtitulo", foreground=C["tag_label"],
                                     font=("Courier New", 10, "bold"))
        w.tag_configure("label",     foreground=C["tag_label"],
                                     font=("Courier New", 10, "bold"))
        w.tag_configure("label_err", foreground=C["tag_err"],
                                     font=("Courier New", 10, "bold"))
        w.tag_configure("label_ok",  foreground=C["tag_ok"],
                                     font=("Courier New", 10, "bold"))
        w.tag_configure("comando",   foreground=C["tag_azul"],
                                     font=("Courier New", 10, "italic"))
        w.tag_configure("stdout",    foreground=C["texto_claro"])
        w.tag_configure("stderr",    foreground=C["tag_err"])
        w.tag_configure("error",     foreground="#FF5555")
        w.tag_configure("ok",        foreground=C["tag_ok"])
        w.tag_configure("no_aplica", foreground="#888888")
        w.tag_configure("no_inst",   foreground=C["tag_err"])
        w.tag_configure("hallazgos", foreground=C["tag_ok"],
                                     font=("Courier New", 10, "bold"))
        w.tag_configure("info",      foreground="#888888")
        w.tag_configure("sep",       foreground=C["tag_sep"])
        w.tag_configure("sep2",      foreground=C["tag_sep2"])
        w.tag_configure("normal",    foreground=C["texto_claro"])

    def _mostrar_tab_bienvenida(self):
        """Pestana inicial de bienvenida con colores XP."""
        frame = tk.Frame(self.notebook, bg=C["fondo_entry"])
        self.notebook.add(frame, text="  Inicio  ")

        # Imagen centrada grande
        img = _cargar_imagen(RUTA_IMAGEN, ancho_max=120, alto_max=100)
        if img:
            self._img_bienvenida = img
            tk.Label(frame, image=self._img_bienvenida,
                     bg=C["fondo_entry"]).pack(pady=(30, 6))
        else:
            tk.Label(frame, text="Viernez13 Stegtools",
                     font=("Tahoma", 26, "bold"),
                     fg=C["rojo"], bg=C["fondo_entry"]).pack(pady=(40, 6))

        tk.Label(
            frame,
            text="Viernez13 Stegtools",
            font=("Tahoma", 20, "bold"),
            fg=C["rojo"], bg=C["fondo_entry"],
        ).pack()

        tk.Label(
            frame,
            text="Herramienta de Analisis Esteganografico",
            font=("Tahoma", 12),
            fg=C["texto_gris"], bg=C["fondo_entry"],
        ).pack(pady=(2, 16))

        info = (
            "Selecciona un archivo de imagen o audio y pulsa ANALIZAR.\n"
            "Las herramientas aplicables se ejecutan automaticamente\n"
            "segun la extension del archivo.\n\n"
            "Para usar una contrasena concreta en steghide:\n"
            "  Desmarca 'Usar fuerza bruta' e ingresa la contrasena.\n\n"
            "Herramientas soportadas:\n"
            "  exiftool   Extraccion de metadatos\n"
            "  binwalk    Deteccion de archivos embebidos\n"
            "  steghide   Extraccion (JPEG / BMP / WAV / AU)\n"
            "  stegseek   Ataque de diccionario (steghide)\n"
            "  zsteg      Canales LSB (PNG / BMP)\n"
            "  pngcheck   Verificacion de integridad PNG\n"
            "  outguess   Extraccion con outguess (JPEG)\n"
        )
        tk.Label(
            frame, text=info,
            font=("Courier New", 10),
            fg=C["texto"], bg=C["fondo_entry"],
            justify=tk.LEFT,
        ).pack(padx=60)

    def _limpiar_notebook(self):
        for tab in self.notebook.tabs():
            self.notebook.forget(tab)

    def _mostrar_resultados(self, resultados: List[dict]):
        self._limpiar_notebook()
        self._crear_tab_resumen(resultados)
        for r in resultados:
            self._crear_tab_herramienta(r)

    def _crear_tab_resumen(self, resultados: List[dict]):
        frame = tk.Frame(self.notebook, bg=C["fondo"])
        self.notebook.add(frame, text="  Resumen  ")

        w = self._texto_con_scroll(frame)
        self._aplicar_tags(w)

        SEP = "=" * 74

        w.insert(tk.END, SEP + "\n", "sep2")
        w.insert(tk.END, "  RESUMEN - Viernez13 StegTools\n", "titulo")
        w.insert(tk.END,
                 f"  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
                 "info")
        w.insert(tk.END, SEP + "\n\n", "sep2")

        w.insert(tk.END,
                 f"  {'HERRAMIENTA':<14}  {'ESTADO':<16}  HALLAZGOS\n",
                 "subtitulo")
        w.insert(tk.END, "  " + "-" * 72 + "\n", "sep")

        for r in resultados:
            nombre = r.get("herramienta", "?")
            if not r.get("aplica", True):
                estado, tag = "NO APLICA      ", "no_aplica"
            elif not r.get("disponible", True):
                estado, tag = "NO INSTALADA   ", "no_inst"
            elif r.get("codigo_retorno", -1) == 0:
                estado, tag = "OK             ", "ok"
            elif r.get("codigo_retorno", 0) == -99:
                estado, tag = "ERROR CRITICO  ", "error"
            else:
                estado, tag = "EJECUTADO      ", "normal"

            hallazgo = r.get("hallazgos", "")[:62]
            w.insert(tk.END, f"  {nombre:<14}  ", "normal")
            w.insert(tk.END, f"{estado}  ", tag)
            w.insert(tk.END, f"{hallazgo}\n", "normal")

        w.insert(tk.END, "  " + SEP + "\n", "sep2")
        w.configure(state=tk.DISABLED)

    def _crear_tab_herramienta(self, resultado: dict):
        nombre = resultado.get("herramienta", "?")

        if not resultado.get("aplica", True):
            prefijo = "[-]"
        elif not resultado.get("disponible", True):
            prefijo = "[!]"
        elif resultado.get("codigo_retorno", -1) == 0:
            prefijo = "[+]"
        else:
            prefijo = "[~]"

        frame = tk.Frame(self.notebook, bg=C["fondo"])
        self.notebook.add(frame, text=f"  {prefijo} {nombre}  ")

        w = self._texto_con_scroll(frame)
        self._aplicar_tags(w)

        SEP  = "=" * 74
        SEP2 = "-" * 74

        w.insert(tk.END, SEP + "\n", "sep2")
        w.insert(tk.END, f"  HERRAMIENTA: {nombre.upper()}\n", "titulo")
        w.insert(tk.END, SEP + "\n\n", "sep2")

        if not resultado.get("aplica", True):
            w.insert(tk.END, "  Estado  : ", "label")
            w.insert(tk.END, "NO APLICA\n", "no_aplica")
            w.insert(tk.END,
                     f"  Detalle : {resultado.get('hallazgos', '')}\n\n",
                     "no_aplica")

        elif not resultado.get("disponible", True):
            w.insert(tk.END, "  Estado  : ", "label")
            w.insert(tk.END, "HERRAMIENTA NO INSTALADA\n", "no_inst")
            if resultado.get("error"):
                w.insert(tk.END, f"  Error   : {resultado['error']}\n", "error")
            w.insert(tk.END,
                     f"  Ayuda   : {resultado.get('hallazgos', '')}\n\n", "info")

        else:
            w.insert(tk.END, "  Comando : ", "label")
            w.insert(tk.END, f"{resultado.get('comando', 'N/A')}\n", "comando")

            codigo = resultado.get("codigo_retorno")
            w.insert(tk.END, "  Retorno : ", "label")
            w.insert(tk.END, f"{codigo}\n", "ok" if codigo == 0 else "stderr")

            w.insert(tk.END,
                     f"  Tiempo  : {resultado.get('timestamp', '')}\n\n", "info")

            if resultado.get("stdout"):
                w.insert(tk.END, SEP2 + "\n", "sep")
                w.insert(tk.END, "  SALIDA ESTANDAR:\n", "label")
                w.insert(tk.END, SEP2 + "\n", "sep")
                w.insert(tk.END, resultado["stdout"].rstrip() + "\n\n", "stdout")

            if resultado.get("stderr"):
                w.insert(tk.END, SEP2 + "\n", "sep")
                w.insert(tk.END, "  STDERR / ADVERTENCIAS:\n", "label_err")
                w.insert(tk.END, SEP2 + "\n", "sep")
                w.insert(tk.END, resultado["stderr"].rstrip() + "\n\n", "stderr")

            if resultado.get("error"):
                w.insert(tk.END,
                         f"  ERROR INTERNO: {resultado['error']}\n\n", "error")

        w.insert(tk.END, SEP + "\n", "sep2")
        w.insert(tk.END, "  HALLAZGOS:\n", "label_ok")
        w.insert(tk.END,
                 f"  {resultado.get('hallazgos', 'Sin informacion.')}\n",
                 "hallazgos")
        w.insert(tk.END, SEP + "\n", "sep2")

        w.configure(state=tk.DISABLED)

    # -----------------------------------------------------------------------
    # Seleccion de archivos
    # -----------------------------------------------------------------------

    def _seleccionar_archivo(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo para analizar",
            filetypes=[
                ("Imagenes", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp"),
                ("Audio",    "*.wav *.au *.mp3 *.ogg"),
                ("Todos",    "*.*"),
            ],
        )
        if ruta:
            self.var_archivo.set(ruta)
            self._set_estado(
                f"Archivo: {os.path.basename(ruta)}", C["verde"])

    def _seleccionar_wordlist(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar wordlist",
            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")],
        )
        if ruta:
            self.var_wordlist.set(ruta)

    # -----------------------------------------------------------------------
    # Analisis
    # -----------------------------------------------------------------------

    def _iniciar_analisis(self):
        ruta = self.var_archivo.get().strip()

        if not ruta:
            messagebox.showwarning(
                "Archivo requerido",
                "Por favor selecciona un archivo antes de analizar.")
            return

        if not os.path.exists(ruta):
            messagebox.showerror("Error", f"El archivo no existe:\n{ruta}")
            return

        # Actualizar wordlist
        wl = self.var_wordlist.get().strip()
        if wl:
            config.WORDLIST_PATH = wl

        # Determinar contrasenas a usar
        contrasenas = self._obtener_contrasenas()

        # Preparar UI
        self._limpiar_notebook()
        self._resultados = []
        self.btn_analizar.configure(state=tk.DISABLED, text="  Analizando...  ")
        self.btn_txt.configure(state=tk.DISABLED)
        self.btn_json.configure(state=tk.DISABLED)
        self._set_estado("Iniciando analisis...", C["naranja"])

        self._hilo = threading.Thread(
            target=self._hilo_analisis,
            args=(ruta, contrasenas),
            daemon=True,
        )
        self._hilo.start()

    def _hilo_analisis(self, ruta: str, contrasenas):
        """Corre en segundo plano."""
        def cb(msg):
            self._cola.put(("progreso", msg))

        try:
            resultados = analizar_archivo(ruta, callback=cb,
                                          contrasenas=contrasenas)
            self._cola.put(("completado", resultados))
        except Exception as exc:
            self._cola.put(("error", str(exc)))

    def _iniciar_polling(self):
        """Revisa la cola cada 100 ms desde el hilo principal."""
        try:
            while True:
                tipo, dato = self._cola.get_nowait()
                if tipo == "progreso":
                    self._set_estado(f"{dato}", C["naranja"])
                elif tipo == "completado":
                    self._resultados = dato
                    self._mostrar_resultados(dato)
                    self.btn_analizar.configure(
                        state=tk.NORMAL, text="  ANALIZAR  ")
                    self.btn_txt.configure(state=tk.NORMAL)
                    self.btn_json.configure(state=tk.NORMAL)
                    self._set_estado("Analisis completado.", C["verde"])
                elif tipo == "error":
                    messagebox.showerror(
                        "Error en el analisis",
                        f"Ocurrio un error inesperado:\n{dato}")
                    self.btn_analizar.configure(
                        state=tk.NORMAL, text="  ANALIZAR  ")
                    self._set_estado(f"Error: {dato}", "#CC0000")
        except queue.Empty:
            pass
        finally:
            self.after(100, self._iniciar_polling)

    # -----------------------------------------------------------------------
    # Ventana Acerca de
    # -----------------------------------------------------------------------

    def _ventana_acerca_de(self):
        """Abre la ventana 'Acerca de' con logo grande y enlace."""
        v = tk.Toplevel(self)
        v.title("Acerca de - Viernez13 StegTools")
        v.geometry("480x540")
        v.resizable(False, False)
        v.configure(bg=C["fondo"])
        v.grab_set()  # modal

        # Franja azul XP en la parte superior
        tk.Frame(v, bg=C["xp_barra"], height=6).pack(fill=tk.X)

        # Titulo de la ventana
        tk.Label(
            v,
            text="Viernez13 StegTools",
            font=("Tahoma", 16, "bold"),
            fg=C["rojo"],
            bg=C["fondo"],
        ).pack(pady=(18, 4))

        # Logo grande centrado
        self._img_about = _cargar_imagen(RUTA_IMAGEN,
                                         ancho_max=200, alto_max=180)
        if self._img_about:
            tk.Label(
                v,
                image=self._img_about,
                bg=C["fondo"],
                relief=tk.FLAT,
            ).pack(pady=(8, 4))
        else:
            tk.Label(
                v,
                text="[ Cybeer.png ]",
                font=("Tahoma", 11),
                fg=C["texto_tenue"],
                bg=C["fondo_panel"],
                relief=tk.GROOVE,
                padx=40, pady=40,
            ).pack(pady=(8, 4))

        # Separador
        tk.Frame(v, bg=C["borde_claro"], height=1).pack(
            fill=tk.X, padx=30, pady=8)

        # Descripcion
        tk.Label(
            v,
            text=(
                "Esta herramienta fue creada por Viernez13\n"
                "para la comunidad Cybeersecurity\n"
                "con mucho amor y dedicacion."
            ),
            font=("Tahoma", 11),
            fg=C["texto"],
            bg=C["fondo"],
            justify=tk.CENTER,
        ).pack(padx=20, pady=(0, 10))

        # Enlace clickeable a la pagina
        lnk = tk.Label(
            v,
            text="www.cybeersecurity.cl",
            font=("Tahoma", 11, "underline"),
            fg=C["azul_claro"],
            bg=C["fondo"],
            cursor="hand2",
        )
        lnk.pack(pady=(0, 4))
        lnk.bind("<Button-1>",
                 lambda e: webbrowser.open(URL_CYBEERSECURITY))
        lnk.bind("<Enter>",
                 lambda e: lnk.configure(fg=C["xp_barra2"]))
        lnk.bind("<Leave>",
                 lambda e: lnk.configure(fg=C["azul_claro"]))

        # Version / copyright
        tk.Label(
            v,
            text="Viernez13 StegTools  |  2026",
            font=("Tahoma", 8),
            fg=C["texto_tenue"],
            bg=C["fondo"],
        ).pack(pady=(2, 10))

        # Boton cerrar
        tk.Frame(v, bg=C["borde_claro"], height=1).pack(
            fill=tk.X, padx=30, pady=4)
        tk.Button(
            v, text="  Cerrar  ",
            command=v.destroy,
            bg=C["btn"], fg=C["texto"],
            activebackground=C["btn_hover"],
            relief=tk.RAISED, font=("Tahoma", 10),
            padx=20, pady=4, cursor="hand2",
        ).pack(pady=10)

    # -----------------------------------------------------------------------
    # Acciones auxiliares
    # -----------------------------------------------------------------------

    def _set_estado(self, msg: str, color: str = None):
        self.var_estado.set(msg)
        if color:
            self.lbl_estado.configure(fg=color)

    def _limpiar_todo(self):
        self.var_archivo.set("")
        self._resultados = []
        self._limpiar_notebook()
        self._mostrar_tab_bienvenida()
        self.btn_txt.configure(state=tk.DISABLED)
        self.btn_json.configure(state=tk.DISABLED)
        self._set_estado(
            "Listo. Selecciona un archivo y pulsa ANALIZAR.", C["verde"])

    def _exportar_txt(self):
        if not self._resultados:
            messagebox.showwarning("Sin datos", "No hay resultados para exportar.")
            return
        ruta = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")],
            initialfile=f"steg_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        )
        if ruta:
            try:
                guardar_reporte_txt(self._resultados, ruta)
                messagebox.showinfo("Exportado", f"Reporte guardado en:\n{ruta}")
            except Exception as exc:
                messagebox.showerror("Error", f"No se pudo guardar:\n{exc}")

    def _exportar_json(self):
        if not self._resultados:
            messagebox.showwarning("Sin datos", "No hay resultados para exportar.")
            return
        ruta = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Todos", "*.*")],
            initialfile=f"steg_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        )
        if ruta:
            try:
                guardar_reporte_json(self._resultados, ruta)
                messagebox.showinfo("Exportado", f"JSON guardado en:\n{ruta}")
            except Exception as exc:
                messagebox.showerror("Error", f"No se pudo guardar:\n{exc}")


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

def lanzar_gui():
    """Inicializa y lanza la ventana principal."""
    app = AplicacionSteg()
    app.mainloop()


if __name__ == "__main__":
    lanzar_gui()
