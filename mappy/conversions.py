import PyQt5
from geopandas import GeoDataFrame
import shapely.wkt
import pandas as pd
from pyproj import CRS
from qgis.core import QgsVectorLayer
import numpy as np
import string


def read_layer(layer: QgsVectorLayer):
    """read a qgis vector layer as a geopandas table"""
    names = [field.name() for field in layer.fields()]
    types = [f.typeName() for f in layer.fields()]
    print(names)
    data = []
    for feature in layer.getFeatures():
        if feature.hasGeometry() is False:
            continue

        wkt = feature.geometry().asWkt()
        s = shapely.wkt.loads(wkt)
        my_dict = {}
        for i, a in enumerate(feature.attributes()):
            if isinstance(a, PyQt5.QtCore.QVariant):
                a = None
            # type = types[i]
            # if type == "Integer64":
            #     tt = int
            # elif type == "Real":
            #     tt = np.double
            # elif type == "String":
            #     tt = str
            #     a = tt(a).encode(encoding='latin1')
            # else:
            #     raise TypeError(f"Type {type} not supported for converions")

            my_dict[names[i]] = a

        my_dict['geometry'] = s
        data.append(my_dict)
    df = pd.DataFrame(data)
    try:
        crs = CRS(int(layer.sourceCrs().geographicCrsAuthId().split(':')[1]))
    except:
        crs = None
    geo_df = GeoDataFrame(df, crs=crs)

    # geo_df = geo_df.dropna(axis=1, how='all')

    return geo_df
