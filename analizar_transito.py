"""
analizar_transito.py
--------------------
Programa de los ESTUDIANTES. No necesita internet ni lightkurve:
solo lee los archivos .csv guardados en la carpeta "datos/"
(columnas: tiempo, flujo).

Al iniciar, escribe el nombre de la estrella (debe estar en la carpeta datos/).
Cada clic marca un punto y muestra su tiempo y su flujo.
Los estudiantes deciden qué puntos marcar, anotan los valores y hacen los cálculos.

Teclas:  u = borrar el último clic     c = borrar todos

Instrucciones de uso:
Para el radio del planeta:
- hax click justo antes del tránsito y Justo después (mientras mas putos tengas mejor será el promedio)
- Haz click en el centro del transito aa ver la profundidad del mismo.
       deltaF= (F(fuera)-F(dentro))/F(fuera) = (Rp/R*)^2

Para el período:
toma valores en el centro de cada transito, ahora nos interesa el tiempo. 
"""

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------
# None = el programa pregunta el nombre de la estrella al iniciar.
# O fíjala aquí, por ejemplo: NOMBRE = "HD 209458"
NOMBRE = None

# True muestra qué recibe el programa en cada clic (útil si algo no responde).
DEPURAR = False

# Busca la carpeta "datos" JUNTO a este script
try:
    BASE = Path(__file__).resolve().parent
except NameError:  # Colab / Jupyter
    BASE = Path.cwd()
CARPETA = BASE / "datos"


# ---------------------------------------------------------------------
# Elegir y cargar los datos
# ---------------------------------------------------------------------
def leer_catalogo():
    """catalogo.json es OPCIONAL: solo aporta nombres más bonitos."""
    ruta = CARPETA / "catalogo.json"
    if ruta.exists():
        return json.loads(ruta.read_text(encoding="utf-8"))
    return {}


def normalizar(texto):
    """'HD 209458', 'hd-209458' y 'HD209458' se consideran iguales."""
    return re.sub(r"[^a-z0-9]", "", texto.lower())


def elegir_dataset(catalogo):
    por_archivo = {v["archivo"]: n for n, v in catalogo.items() if "archivo" in v}
    archivos = sorted(f.name for f in CARPETA.glob("*.csv"))
    if not archivos:
        raise SystemExit(f"No hay archivos .csv en {CARPETA}. "
                         "Copia la carpeta 'datos' junto a este programa.")
    opciones = [(por_archivo.get(a, Path(a).stem), a) for a in archivos]

    def buscar(texto):
        buscado = normalizar(texto)
        if not buscado:
            return None
        for nombre, archivo in opciones:
            if buscado in (normalizar(nombre), normalizar(Path(archivo).stem)):
                return nombre, archivo
        return None

    if NOMBRE:
        encontrado = buscar(NOMBRE)
        if encontrado:
            return encontrado
        print(f"'{NOMBRE}' no está en la carpeta datos/.")

    while True:
        try:
            texto = input("\nEscribe el nombre de la estrella (ej. HD 209458): ").strip()
        except EOFError:
            raise SystemExit("No se escribió ninguna estrella.")
        encontrado = buscar(texto)
        if encontrado:
            return encontrado

        # No coincide: sugerir nombres parecidos o mostrar los disponibles
        parecidos = [n for n, _ in opciones if normalizar(texto) and normalizar(texto) in normalizar(n)]
        if texto and parecidos:
            print(f"'{texto}' no coincide exactamente. ¿Quisiste decir: {', '.join(parecidos)}?")
        else:
            print(f"'{texto}' no está en la carpeta datos/." if texto else "No escribiste nada.")
            print("Estrellas disponibles: " + ", ".join(n for n, _ in opciones))


nombre, archivo = elegir_dataset(leer_catalogo())

datos = pd.read_csv(CARPETA / archivo)
time = datos["tiempo"].values
flux = datos["flujo"].values
flux_suave = pd.Series(flux).rolling(15, center=True, min_periods=1).median().values

# ---------------------------------------------------------------------
# Gráfica
# ---------------------------------------------------------------------
# En IPython se usa el modo interactivo; en una terminal normal,
# plt.show() espera los clics.
try:
    get_ipython()  # type: ignore
    EN_IPYTHON = True
except NameError:
    EN_IPYTHON = False

if EN_IPYTHON:
    plt.ion()

fig, ax = plt.subplots(figsize=(11, 5))
ax.plot(time, flux, ".", alpha=0.3, label="Flujo normalizado")
ax.plot(time, flux_suave, color="red", lw=1, label="Flujo suavizado")
ax.set_xlabel("Tiempo (días)")
ax.set_ylabel("Flujo normalizado")
ax.set_title(f"{nombre}  |  Haz clic para marcar puntos   "
             "(u = borrar el último, c = borrar todos)", fontsize=10)
ax.legend(loc="lower right")

clicks = []  # (tiempo, flujo) de cada clic
marcas = []  # dibujos de cada clic, para poder borrarlos


def herramienta_activa():
    """True si el zoom o el mover de la barra de herramientas está activo."""
    barra = getattr(fig.canvas, "toolbar", None)
    modo = getattr(barra, "mode", "")
    modo = getattr(modo, "value", modo)  # algunas versiones usan un Enum
    return bool(str(modo).strip())


def al_hacer_clic(event):
    if DEPURAR:
        print(f"[depuración] clic recibido, dentro de la gráfica: {event.inaxes is ax}")
    if event.inaxes != ax:
        return
    if herramienta_activa():
        if DEPURAR:
            print("[depuración] clic ignorado: hay una herramienta de zoom/mover activa")
        return

    # Se toma el dato real más cercano al clic
    idx = np.abs(time - event.xdata).argmin()
    t, f = time[idx], flux[idx]

    clicks.append((t, f))
    n = len(clicks)
    print(f"#{n}  tiempo = {t:.4f} d  |  flujo = {f:.5f}")

    linea = ax.axvline(t, color="green", ls="--", lw=0.8)
    nota = ax.annotate(
        f"#{n}  t={t:.4f}  f={f:.5f}",
        xy=(t, f), xytext=(8, 10 + 14 * ((n - 1) % 3)), textcoords="offset points",
        fontsize=7, bbox=dict(boxstyle="round", facecolor="yellow", alpha=0.85),
        arrowprops=dict(arrowstyle="->"),
    )
    marcas.append((linea, nota))
    fig.canvas.draw_idle()


def al_presionar_tecla(event):
    if event.key == "u" and clicks:
        clicks.pop()
        for dibujo in marcas.pop():
            dibujo.remove()
        print(f"Clic borrado. Quedan {len(clicks)}.")
        fig.canvas.draw_idle()
    elif event.key == "c" and clicks:
        for linea, nota in marcas:
            linea.remove()
            nota.remove()
        clicks.clear()
        marcas.clear()
        print("Todos los clics borrados.")
        fig.canvas.draw_idle()


fig.canvas.mpl_connect("button_press_event", al_hacer_clic)
fig.canvas.mpl_connect("key_press_event", al_presionar_tecla)

backend = matplotlib.get_backend()
print(f"\nBackend gráfico: {backend} | IPython: {EN_IPYTHON}")
if backend.lower() == "agg" or "inline" in backend.lower():
    print("AVISO: la gráfica NO es interactiva.")
    print("En IPython escribe primero:  %matplotlib qt   (o  %matplotlib tk)")
    print("y luego vuelve a ejecutar el programa.")



def mostrar_instrucciones():
    linea = "=" * 62
    print(f"""
{linea}
 {nombre}  -  GUÍA RÁPIDA
{linea}

RADIO DEL PLANETA
  1. Haz clic en varios puntos ANTES y DESPUÉS del tránsito
     (brillo normal de la estrella).
  2. Haz clic en varios puntos DENTRO del tránsito
     (la parte más baja).
  3. Anota los valores y promedia cada grupo:
        F_fuera   (antes y después)
        F_dentro
  4. Calcula:
        profundidad = (F_fuera - F_dentro) / F_fuera
        Rp / R*     = raíz cuadrada(profundidad)
        Rp          = (Rp / R*) x R*
     R* = radio de la estrella: investígalo y anota la fuente.

PERÍODO
  1. Haz clic en el CENTRO de varios tránsitos seguidos.
  2. Período = tiempo del centro 2 - tiempo del centro 1
     (con varios, promedia las diferencias).

TECLAS
  u = borrar el último clic       c = borrar todos
  Para acercarte usa la lupa, y DESACTÍVALA antes de hacer clic.
  Para terminar, cierra la ventana de la gráfica.
{linea}
""")


mostrar_instrucciones()

plt.show(block=not EN_IPYTHON)
