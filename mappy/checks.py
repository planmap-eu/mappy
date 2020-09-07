from mappy import log
import geopandas

def check_validity_of_geometries(data: geopandas.GeoDataFrame):
    for pol in data.geometry:
        if not pol.is_valid:
            log.warning("found invalid geometry")

