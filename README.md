# Viernez13 StegTools

Herramienta de analisis esteganografico multi-motor para archivos de imagen y audio.
Combina siete herramientas del ecosistema de esteganografia en una unica interfaz
CLI y GUI, organizando los resultados de forma clara y exportandolos como TXT o JSON.
<img width="1913" height="984" alt="image" src="https://github.com/user-attachments/assets/961d181a-a578-4499-a920-dbded62fc279" />

## Herramientas externas requeridas

Instala las que tengas disponibles. El programa funciona aunque alguna no este presente:
simplemente la marcara como "NO INSTALADA" y continuara con las demas.

```bash
# Debian / Ubuntu / Kali
sudo apt install libimage-exiftool-perl   # exiftool
sudo apt install binwalk                  # binwalk
sudo apt install steghide                 # steghide
sudo apt install pngcheck                 # pngcheck
sudo apt install outguess                 # outguess

# zsteg (requiere Ruby)
sudo apt install ruby
sudo gem install zsteg

# stegseek (descargar el .deb desde GitHub Releases)
# https://github.com/RickdeJager/stegseek/releases
wget https://github.com/RickdeJager/stegseek/releases/download/v0.6/stegseek_0.6-1.deb
sudo dpkg -i stegseek_0.6-1.deb

# Para la GUI de Tkinter (si no esta disponible)
sudo apt install python3-tk
```

---

## Configuracion

Edita `analizador/config.py` antes de ejecutar para ajustar:

| Variable              | Descripcion                                        | Valor por defecto                   |
|-----------------------|----------------------------------------------------|-------------------------------------|
| `WORDLIST_PATH`       | Ruta a la wordlist para stegseek                   | `/usr/share/wordlists/rockyou.txt`  |
| `CONTRASENAS_COMUNES` | Lista de contrasenas a probar con steghide         | password, 123456, secret...         |
| `TIMEOUT_HERRAMIENTA` | Tiempo maximo por herramienta (segundos)           | `120`                               |
| `DIRECTORIO_SALIDA`   | Directorio donde se guardan archivos extraidos     | `/tmp/steganalisis_output`          |

---

## Instalacion de dependencias Python

No se requieren paquetes externos. Solo Python 3.8 o superior con Tkinter:

```bash
python3 --version        # verificar version
python3 -c "import tkinter; print('Tkinter OK')"
```

Si Tkinter no esta disponible:

```bash
sudo apt install python3-tk
```

---

## Uso - Linea de comandos (CLI)

```bash
# Analizar un archivo (salida en consola)
python3 main.py imagen.jpg

# Guardar reporte en texto y JSON
python3 main.py imagen.jpg -o reporte.txt -j reporte.json

# Usar una wordlist personalizada para stegseek
python3 main.py imagen.jpg --wordlist /ruta/a/rockyou.txt

# Ver ayuda completa
python3 main.py --help
```

Ejemplo de salida CLI:

```
========================================================================
  Viernez13 StegTools - Analisis Esteganografico
========================================================================
  Archivo  : /home/usuario/imagen.jpg
  Tamano   : 204,800 bytes
========================================================================

  >> [1/7] Ejecutando exiftool...
  >> [1/7] exiftool completado.
  ...

========================================================================
  HERRAMIENTA: EXIFTOOL
========================================================================
  Comando    : exiftool imagen.jpg
  Retorno    : 0
  ...
  HALLAZGOS: Se extrajeron 34 campos de metadatos.
```

---

## Uso - Interfaz grafica (GUI)

```bash
# Opcion 1: desde main.py
python3 main.py --gui

# Opcion 2: directamente
python3 gui.py
```

La GUI incluye:

- **Titulo** "Viernez13 Stegtools" en rojo
- **Campo de archivo** con boton Examinar para seleccionar el objetivo
- **Campo de wordlist** editable con boton Examinar
- **Boton ANALIZAR** que lanza el analisis en segundo plano
- **Pestanas por herramienta** con la salida completa de cada una
- **Pestana Resumen** con tabla de estado de todas las herramientas
- **Botones de exportacion** para guardar el reporte en TXT o JSON

---

## Ejemplo de uso completo

```bash
# 1. Clonar o descargar el proyecto
cd /home/usuario/steganalisis

# 2. Verificar herramientas disponibles
which exiftool binwalk steghide stegseek zsteg pngcheck outguess

# 3. Analizar una imagen sospechosa
python3 main.py /ruta/a/imagen_sospechosa.jpg -o reporte.txt -j reporte.json

# 4. O abrir la GUI
python3 main.py --gui
```
<img width="1913" height="984" alt="image" src="https://github.com/user-attachments/assets/383e52d5-c4f0-4f38-a3f9-1ab865e50c4b" />

---

## Herramientas y formatos soportados

| Herramienta | JPEG | PNG | BMP | WAV | AU |
|-------------|:----:|:---:|:---:|:---:|:--:|
| exiftool    |  SI  | SI  | SI  | SI  | SI |
| binwalk     |  SI  | SI  | SI  | SI  | SI |
| steghide    |  SI  |  -  | SI  | SI  | SI |
| stegseek    |  SI  |  -  | SI  | SI  | SI |
| zsteg       |  -   | SI  | SI  |  -  |  - |
| pngcheck    |  -   | SI  |  -  |  -  |  - |
| outguess    |  SI  |  -  |  -  |  -  |  - |

---

## Notas de seguridad

- `subprocess` se usa siempre con listas de argumentos (nunca `shell=True` con
  entrada del usuario), evitando inyeccion de comandos.
- Los archivos extraidos se guardan en `/tmp/steganalisis_output/` con nombres
  unicos por PID para evitar colisiones.
- Ninguna herramienta escribe fuera de ese directorio.

---

## Autor

**Viernez13** - Proyecto de analisis esteganografico educativo.
