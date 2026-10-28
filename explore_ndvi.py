"""Settimana 1: esplorazione dell'NDVI degli uliveti pugliesi, 2017-2025.

Confronta il Salento (colpito presto dalla Xylella) con l'area di Bari
(colpita poco o niente), anno per anno, e apre una mappa della variazione.
"""
import os
import webbrowser

import ee
from dotenv import load_dotenv

load_dotenv()
ee.Initialize(project=os.environ["EE_PROJECT"])

# Aree di interesse: rettangoli [lon_min, lat_min, lon_max, lat_max]
PUGLIA = ee.Geometry.Rectangle([14.9, 39.7, 18.6, 42.3])
SALENTO = ee.Geometry.Rectangle([17.9, 39.8, 18.5, 40.4])  # colpito presto
BARI = ee.Geometry.Rectangle([16.5, 40.9, 17.0, 41.2])     # gruppo di controllo
AREAS = {"Salento": SALENTO, "Bari": BARI}

YEARS = range(2017, 2026)
MAP_START, MAP_END = 2017, 2025

# Maschera uliveti: CORINE Land Cover 2018, classe 223 = oliveti
OLIVE_MASK = ee.Image("COPERNICUS/CORINE/V20/100m/2018").select("landcover").eq(223)


def mask_clouds(img):
    """Toglie nuvole e ombre usando la banda SCL (classi 3, 8, 9, 10)."""
    scl = img.select("SCL")
    clear = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
    return img.updateMask(clear)


def july_ndvi(year):
    """NDVI mediano di luglio sugli uliveti, per l'anno dato."""
    images = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(PUGLIA)
        .filterDate(f"{year}-07-01", f"{year}-08-01")
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 40))
        .map(mask_clouds)
    )
    ndvi = images.median().normalizedDifference(["B8", "B4"]).rename("NDVI")
    return ndvi.updateMask(OLIVE_MASK)


def mean_in_area(image, area, band):
    """Valore medio di una banda dentro un'area (a 100 m per risparmiare quota)."""
    stats = image.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=area, scale=100, maxPixels=1e9
    ).getInfo()
    return stats[band]


def print_yearly_table():
    """NDVI medio per anno nelle due aree, e la loro differenza."""
    print("Anno | Salento | Bari  | Differenza (Salento - Bari)")
    print("-----+---------+-------+----------------------------")
    for year in YEARS:
        ndvi = july_ndvi(year)
        salento = mean_in_area(ndvi, SALENTO, "NDVI")
        bari = mean_in_area(ndvi, BARI, "NDVI")
        print(f"{year} | {salento:.3f}   | {bari:.3f} | {salento - bari:+.3f}")


def open_change_map():
    """Mappa della variazione di NDVI: rosso = perdita, bianco = nessun cambio, verde = guadagno."""
    change = july_ndvi(MAP_END).subtract(july_ndvi(MAP_START)).rename("change")

    print(f"\nVariazione media NDVI {MAP_START} -> {MAP_END}:")
    for name, area in AREAS.items():
        print(f"  {name}: {mean_in_area(change, area, 'change'):+.3f}")

    url = change.getThumbURL({
        "region": PUGLIA,
        "dimensions": 1024,
        "min": -0.2,
        "max": 0.2,   # scala simmetrica: il bianco corrisponde a zero
        "palette": ["red", "white", "green"],
    })
    webbrowser.open(url)


if __name__ == "__main__":
    print_yearly_table()
    open_change_map()