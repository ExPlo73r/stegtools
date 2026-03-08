"""
Configuracion global del proyecto StegAnalisis.
Modifica estas variables segun tu entorno antes de ejecutar.
"""

# ---------------------------------------------------------------------------
# Wordlist para stegseek (y para ataques de diccionario futuros)
# Cambia esta ruta a la ubicacion real de tu wordlist
# ---------------------------------------------------------------------------
WORDLIST_PATH = "/usr/share/wordlists/rockyou.txt"

# ---------------------------------------------------------------------------
# Contrasenas comunes para intentar con steghide
# Se prueban en orden; la primera que funcione detiene el bucle
# ---------------------------------------------------------------------------
CONTRASENAS_COMUNES = [
    "",            # Contrasena vacia (muy comun)
    "password",
    "123456",
    "secret",
    "hidden",
    "steg",
    "steghide",
    "admin",
    "root",
    "pass",
    "1234",
    "abcd",
    "qwerty",
    "letmein",
    "abc123",
]

# ---------------------------------------------------------------------------
# Timeout maximo por herramienta (en segundos)
# Aumenta si usas wordlists muy grandes o hardware lento
# ---------------------------------------------------------------------------
TIMEOUT_HERRAMIENTA = 120

# ---------------------------------------------------------------------------
# Directorio donde se guardan los archivos extraidos por las herramientas
# ---------------------------------------------------------------------------
DIRECTORIO_SALIDA = "/tmp/steganalisis_output"
