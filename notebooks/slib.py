
from shapely.geometry import MultiLineString,GeometryCollection,MultiPolygon,MultiPoint, Point, LineString, Polygon
from geopandas import GeoDataFrame
import logging as log

def explode(geom):
    out = []
    if isinstance(geom, (MultiLineString, GeometryCollection, MultiPolygon, MultiPoint)):
        for i in geom:
            out += explode(i)
            
        return out
    else:
        return [geom]
            
def filter_by_type(geoms):
    lines = []
    points = []
    polygons = []
    for g in geoms:
        if isinstance(g,Point):
            points.append(g)
        elif isinstance(g,LineString):
            lines.append(g)
        elif isinstance(g,Polygon):
            polygons.append(g)
        else:
            log.warning(f"no implmentation for {type(g)}")
            
    return points, lines, polygons

def asGdf(geoms, crs=None):
    gdf = GeoDataFrame(crs=crs)
    gdf.geometry=geoms
    return gdf