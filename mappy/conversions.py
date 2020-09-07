from geopandas import GeoDataFrame
import shapely.wkt
import pandas as pd
from pyproj import CRS
from qgis.core import QgsVectorLayer

def read_layer(layer:QgsVectorLayer):
    """read a qgis vector layer as a geopandas table"""
    names = [field.name() for field in layer.fields()]
    print(names)
    data = []
    for feature in layer.getFeatures():
        if feature.hasGeometry() is False:
            continue

        wkt = feature.geometry().asWkt()
        s = shapely.wkt.loads(wkt)
        my_dict = {}
        for i, a in enumerate(feature.attributes()):
            my_dict[names[i]] = a

        my_dict['geometry'] = s
        data.append(my_dict)
    df = pd.DataFrame(data)
    crs = CRS(int(layer.sourceCrs().geographicCrsAuthId().split(':')[1]))
    geo_df = GeoDataFrame(df, crs=crs)

    return geo_df