"""
descargar_datos.py
------------------
Programa del FACILITADOR. Necesita internet y lightkurve (pip install lightkurve).
Descarga la curva de luz de CUALQUIER estrella y la guarda en la carpeta "datos/"
para que los estudiantes la usen con analizar_transito.py (sin internet).

Cómo funciona:
  1. Escribes el nombre de la estrella (ej. HD 209458) y, si quieres, el planeta (ej. b).
  2. Si hay datos de varios catálogos (SPOC, QLP, Kepler...), el programa te los
     muestra y eliges uno.
  3. Eliges el sector/cuarto (Enter = el primero).

Se puede ejecutar así:
    python descargar_datos.py                       -> te pregunta todo
    python descargar_datos.py "WASP-18" "HD 209458" -> empieza con esas estrellas
    (en IPython:  %run descargar_datos.py WASP-18)

Resultado:
    datos/<estrella>_<planeta>_<catalogo>.csv    columnas: tiempo, flujo, error
        ejemplo:  datos/HD209458_b_SPOC.csv
    datos/catalogo.json    datos extra para ti (NO es necesario compartirlo)
"""

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import lightkurve as lk

# La carpeta "datos" se crea JUNTO a este script (no donde abras la terminal)
try:
    BASE = Path(__file__).resolve().parent
except NameError:  # Colab / Jupyter, donde __file__ no existe
    BASE = Path.cwd()
CARPETA = BASE / "datos"
CARPETA.mkdir(exist_ok=True)


# ---------------------------------------------------------------------
# Preguntas al usuario
# ---------------------------------------------------------------------
def preguntar(texto, defecto=""):
    try:
        respuesta = input(texto).strip()
    except EOFError:
        respuesta = ""
    return respuesta or defecto


def elegir_numero(texto, maximo):
    """Pide un número entre 1 y maximo (Enter = 1)."""
    while True:
        r = preguntar(texto, "1")
        if r.isdigit() and 1 <= int(r) <= maximo:
            return int(r) - 1
        print(f"  Escribe un número del 1 al {maximo}.")


def limpiar(texto):
    """Para nombres de archivo: solo letras y números."""
    return re.sub(r"[^A-Za-z0-9]+", "", texto)


# ---------------------------------------------------------------------
# Búsqueda
# ---------------------------------------------------------------------
def columna(tabla, nombre, i, defecto="?"):
    if nombre in tabla.colnames:
        return str(tabla[nombre][i]).strip()
    return defecto


def agrupar_por_catalogo(busqueda):
    """Agrupa los resultados por (misión, catálogo/autor). Devuelve una lista de dicts."""
    tabla = busqueda.table
    grupos = {}
    for i in range(len(tabla)):
        mision = columna(tabla, "project", i, columna(tabla, "mission", i))
        autor = columna(tabla, "author", i)
        grupos.setdefault((mision, autor), []).append(i)
    lista = []
    for (mision, autor), indices in grupos.items():
        tiempos = sorted({columna(tabla, "exptime", i) for i in indices})
        lista.append({"mision": mision, "autor": autor,
                      "indices": indices, "exptime": ", ".join(tiempos)})
    # SPOC y Kepler primero: suelen ser los más limpios
    prioridad = {"SPOC": 0, "Kepler": 1}
    lista.sort(key=lambda g: (prioridad.get(g["autor"], 9), g["autor"]))
    return lista


def elegir_catalogo(busqueda):
    grupos = agrupar_por_catalogo(busqueda)
    if len(grupos) == 1:
        g = grupos[0]
        print(f"  Un solo catálogo disponible: {g['autor']} ({g['mision']}).")
        return g
    print("\n  Catálogos disponibles para esta estrella:")
    for n, g in enumerate(grupos, 1):
        print(f"    {n}. {g['autor']:<10} misión {g['mision']:<8} "
              f"{len(g['indices'])} observaciones   exposición (s): {g['exptime']}")
    return grupos[elegir_numero("  Elige el catálogo (Enter = 1): ", len(grupos))]


def elegir_observacion(busqueda, grupo):
    indices = grupo["indices"]
    if len(indices) == 1:
        return indices[0]
    tabla = busqueda.table
    print("\n  Observaciones (sectores/cuartos) en ese catálogo:")
    for n, i in enumerate(indices, 1):
        print(f"    {n}. {columna(tabla, 'mission', i)}   exposición: {columna(tabla, 'exptime', i)} s")
    return indices[elegir_numero("  Elige una (Enter = 1): ", len(indices))]


def descargar(nombre):
    """Busca, deja elegir catálogo y observación, y devuelve (curva limpia, nombre del catálogo)."""
    print("  Buscando datos...")
    busqueda = lk.search_lightcurve(nombre)
    if len(busqueda) == 0:
        return None, None

    grupo = elegir_catalogo(busqueda)
    i = elegir_observacion(busqueda, grupo)
    print("  Descargando...")
    lc = busqueda[i].download()
    lc = lc.remove_nans().normalize()
    # Quita solo puntos anormalmente ALTOS, para no borrar el tránsito
    lc = lc.remove_outliers(sigma_upper=4, sigma_lower=20)
    return lc, grupo["autor"]


def radio_de_la_estrella(lc):
    """Radio estelar (en radios solares) que el archivo incluye, si existe."""
    try:
        radio = float(lc.meta.get("RADIUS"))
        return radio if np.isfinite(radio) and radio > 0 else None
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------
def main():
    ruta_catalogo = CARPETA / "catalogo.json"
    catalogo = json.loads(ruta_catalogo.read_text(encoding="utf-8")) if ruta_catalogo.exists() else {}

    pendientes = [a for a in sys.argv[1:] if not a.startswith("-")]

    while True:
        if pendientes:
            nombre = pendientes.pop(0)
            print(f"\nEstrella: {nombre}")
        else:
            nombre = preguntar("\nNombre de la estrella (Enter = terminar): ")
            if not nombre:
                break

        planeta = preguntar("Letra o nombre del planeta (ej. b; Enter = sin planeta): ")

        try:
            lc, autor = descargar(nombre)
        except Exception as e:
            print(f"  Error al descargar {nombre}: {e}")
            continue
        if lc is None:
            print(f"  No se encontraron datos para '{nombre}'. Revisa cómo está escrito.")
            continue

        partes = [limpiar(nombre), limpiar(planeta), limpiar(autor)]
        archivo = "_".join(p for p in partes if p) + ".csv"
        df = pd.DataFrame({
            "tiempo": np.asarray(lc.time.value),
            "flujo": np.asarray(lc.flux.value),
            "error": np.asarray(lc.flux_err.value),
        })
        df.to_csv(CARPETA / archivo, index=False)

        entrada = {"estrella": nombre, "planeta": planeta, "catalogo": autor,
                   "sector": int(lc.meta.get("SECTOR", lc.meta.get("QUARTER", -1)) or -1)}
        radio = radio_de_la_estrella(lc)
        if radio is not None:
            entrada["r_estrella_rsol"] = round(radio, 3)
        catalogo[Path(archivo).stem] = {**catalogo.get(Path(archivo).stem, {}), **entrada}

        print(f"  Guardado {archivo} ({len(df)} puntos)")
        if radio is None:
            print("  (El archivo no trae el radio de la estrella.)")

    ruta_catalogo.write_text(json.dumps(catalogo, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nListo. Los datos están en esta carpeta:\n  {CARPETA}")
    print("Copia esa carpeta 'datos' junto a analizar_transito.py")


if __name__ == "__main__":
    main()