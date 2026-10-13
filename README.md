# Explorando tránsitos exoplanetarios por Dra. Breezy Ocaña Flaquer

Taller de astronomía para estudiantes de los últimos años de secundaria: con **datos reales de telescopios espaciales de la NASA (TESS, Kepler y K2)** miden la caída de brillo de una estrella cuando un planeta pasa por delante (un *tránsito*) y calculan, con su calculadora, el **radio** y el **período** del planeta.

*Astronomía para todos · Fundación GenerAcciones · AstroEduRD y NAEC *


## Opción 1 · Sin instalar nada (Google Colab)

Solo necesitas una cuenta de Google.

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/BreezyOF/explorando-transitos/blob/main/analizar_transito_colab.ipynb)

1. Abre el enlace y ejecuta las celdas **en orden** con el botón ▶.
2. Escribe el nombre de la estrella y pasa el cursor sobre la gráfica para leer tiempo y flujo.
3. Anota los valores y haz los cálculos a mano.

## Opción 2 · En tu computadora (Python)

1. Instala [Python 3](https://www.python.org/downloads/) y, en una terminal:
   ```
   pip install numpy pandas matplotlib
   ```
2. Descarga este repositorio (botón verde **Code → Download ZIP**) y descomprímelo.
3. Ejecuta:
   ```
   python analizar_transito.py
   ```
4. Escribe el nombre de la estrella (debe estar en la carpeta `datos/`) y haz clic en la gráfica para marcar puntos.
   - `u` borra el último clic · `c` borra todos
   - Si usas la lupa para acercarte, desactívala antes de hacer clic.
   - Para terminar, cierra la ventana de la gráfica.

## Qué hay aquí

| Archivo | Para qué sirve |
|---|---|
| `analizar_transito.py` | Programa de los estudiantes (usa los datos de `datos/`, sin internet) |
| `analizar_transito_colab.ipynb` | Versión para Google Colab |
| `descargar_datos.py` | Programa del facilitador: descarga curvas de luz de cualquier estrella desde los telescopios TESS, Kepler y K2, y te deja elegir el catálogo (necesita `lightkurve`) |
| `datos/` | Curvas de luz ya descargadas (`tiempo`, `flujo`), con nombre `estrella_planeta_catálogo.csv` |

## Para el facilitador: añadir otras estrellas

```
pip install lightkurve
python descargar_datos.py
```

El programa te pide el nombre de la estrella y del planeta; si hay datos en varios catálogos (SPOC, QLP, Kepler…) te los muestra para que elijas. Se crea, junto al programa, un archivo con el formato `datos/<estrella>_<planeta>_<catálogo>.csv` (por ejemplo `HD209458_b_SPOC.csv`). Súbelo al repositorio para que aparezca también en Colab.

## Créditos

Datos de las misiones TESS, Kepler y K2 (NASA), obtenidos del archivo MAST (Space Telescope Science Institute) mediante [lightkurve](https://docs.lightkurve.org/).
