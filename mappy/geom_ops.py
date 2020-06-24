import logging as log

import geopandas
import numpy as np
import shapely.ops
from shapely.geometry import LineString, MultiLineString, GeometryCollection, MultiPolygon, MultiPoint


def explode(geom):
    out = []
    if isinstance(geom, (MultiLineString, GeometryCollection, MultiPolygon, MultiPoint)):
        for i in geom:
            out += explode(i)

        return out
    else:
        return [geom]


def extend(p1: np.ndarray, p2: np.ndarray, distance: float):
    """
    from p1 to p2 extended by dist.
    """
    if np.linalg.norm(p2 - p1) < 1e-16:
        log.warning("two points are equal, cannot extend")
        raise ValueError("two points are equal, cannot extend")
    v = p2 - p1
    v = v / np.linalg.norm(v) * distance

    news = p2 + v
    return news


def drop_duplicated_points(points: np.ndarray, threshold=1e-8):
    """
    remove consecutive duplicated points from a list of points
    :param points:
    :param threshold:
    :return:
    """
    clean = []
    for pt in points:
        if len(clean) > 0:
            if np.linalg.norm(pt - clean[-1]) > threshold:
                clean.append(pt)
        else:
            clean.append(pt)

    clean = np.array(clean)

    return clean


def extend_lines(geodataframe: geopandas.GeoDataFrame, distance: float):
    """
    Extends begin and end segments of the line by the given distance.
    :param geodataframe:
    :param distance:
    :return:
    """
    from copy import deepcopy
    outframe = deepcopy(geodataframe)

    out = []  # the collection of extended LineStrings
    for f in geodataframe.geometry:
        if f.is_closed is True:
            log.warning("shape is closed. skip - no need to extend it")
            l = LineString(np.row_stack([f.xy]).T)
            out.append(l)
            continue

        if not f.is_valid:  # if the shape is no valid for some reason we remove it.
            log.warning("a not valid shape was found")
            raise ValueError("a not valid shape was found")

        pts = np.row_stack([f.xy]).T

        pts = drop_duplicated_points(
            pts)  # be sure we dont' have duplicated points wich might
        # be a problem expecially at the end and beginning (we would not be able to extend the feature)

        start = pts[:2][::-1]
        end = pts[::-1][:2][::-1]

        news = extend(start[0], start[1], distance)
        newe = extend(end[0], end[1], distance)

        extended = np.row_stack([news, pts, newe])

        if np.isnan(extended).any():
            print("Containing nans")

        l = LineString(extended)
        if not l.is_valid:
            log.warning("line not valid")
        out.append(l)

    outframe["geometry"] = out

    return outframe


def compute_self_intersections_points(geodataframe: geopandas.GeoDataFrame):
    """
    Find the points of self intersections of the lines
    :param geodataframe:
    :return:
    """
    ints = []

    for geom in geodataframe.geometry:
        ii = geodataframe.intersection(geom)
        for i in ii:
            if i.type == "MultiPoint":
                ints.extend(i)  # appends multiple items from iterator to the list
            elif i.type == "Point":
                ints.append(i)
            # else:
            #     log.warning(f"skipping intersection because of unsupported type {i.type}")

    return geopandas.GeoDataFrame(geometry=ints)


def polygonize(lines: geopandas.GeoDataFrame) -> geopandas.GeoDataFrame:
    """
    Perform polygonyze of the lines (lines -> polygons)
    :param lines:
    :return:
    """
    unified = shapely.ops.cascaded_union(lines.geometry)
    pols = list(shapely.ops.polygonize(unified))
    polygons = geopandas.GeoDataFrame(geometry=pols)
    return polygons


def get_points_inside(polygon, points):
    """
    commodity function to get the ids of points falling within a polygon
    \note for now only Polygon is considered. - not MultiP
    """
    out = []
    for id, p in enumerate(points):
        if p.within(polygon):
            out.append(id)

    return out


def transfer_units_to_polygons(polygons: geopandas.GeoDataFrame, units: geopandas.GeoDataFrame, units_field: str):
    """
    this could be obtained with a spatial joint, but with this we have more control to perform checks and know what is going on
    e.g. geopandas.sjoin( polygons, units, how="left", op='contains').plot(column= units_field)
    :param polygons:
    :param units:
    :param units_field:
    :return: A copy of polygons with the units
    """
    outids = []
    for pol in polygons.geometry:
        ids = get_points_inside(pol, units.geometry)
        log.info(f"found {len(ids)} ids: {ids}")
        thisunit = units[units_field][ids].values
        log.info(f"thisunit {thisunit}")

        if len(ids) > 1:
            log.warning("more than two points were found in the same polygon")

            if np.all(thisunit == thisunit[0]):
                log.warning("no prob, because point to the same unit")

        if len(ids) < 1:
            log.error("cannot associate some polygons to an unit, missing points in unit definition file?")
            thisunit = [None]

        myunit = thisunit[0]
        outids.append(myunit)
    from copy import deepcopy
    out_polygons = deepcopy(polygons)
    out_polygons[units_field] = outids
    return out_polygons
