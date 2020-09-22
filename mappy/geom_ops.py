from mappy import log
import geopandas
import numpy as np
import shapely.ops
from shapely.geometry import LineString, MultiLineString, GeometryCollection, MultiPolygon, MultiPoint, Polygon
from shapely.ops import polylabel
import fiona, os


def explode(geom):
    out = []
    if isinstance(geom, (MultiLineString, GeometryCollection, MultiPolygon, MultiPoint)):
        for i in geom:
            out += explode(i)

        return out
    else:
        return [geom]


def explode_all(geometries):
    out = []
    for g in geometries:
        out += explode(g)
    return out


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

    allg = explode_all(geodataframe.geometry)
    geodataframe = geopandas.GeoDataFrame(geometry=allg)
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
            log.warning("Extended line containing nans, should not happen")

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
    out = geopandas.GeoDataFrame(geometry=ints)
    out.crs = geodataframe.crs  # copy crs over
    return out


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

            else:
                log.warning("The unit contains points with mismatched indicator points. Setting to None")
                thisunit = [None]

        if len(ids) < 1:
            log.error("cannot associate some polygons to an unit, missing points in unit definition file?")
            thisunit = [None]

        myunit = thisunit[0]
        outids.append(myunit)

    from copy import deepcopy
    out_polygons = deepcopy(polygons)
    out_polygons[units_field] = outids
    return out_polygons


def explode_multipolygons(polygons: geopandas.GeoDataFrame):
    return polygons.explode()


def mappy_polylabel(polygon):
    if not isinstance(polygon, Polygon):
        raise TypeError(f"Only polygons are supported, while geometry was {type(pol)}")
    return polylabel(polygon, tolerance=0.1)


def generate_label_points(polygons: geopandas.GeoDataFrame):
    import multiprocessing
    pool = multiprocessing.Pool()
    labels = pool.map(mappy_polylabel, polygons.geometry)
    pool.close()
    aspd = geopandas.GeoDataFrame(geometry=labels)
    return aspd


def transfer_polygons_fields_to_points(points: geopandas.GeoDataFrame, polygons: geopandas.GeoDataFrame):
    with_fields = geopandas.sjoin(points, polygons)
    if "fid" in with_fields.columns:
        with_fields = with_fields.drop("fid", axis=1)  # remove the additional fid column that has been copied over
    return with_fields


def remove_null_geometries(data: geopandas.GeoDataFrame):
    nulls = data.geometry.values == None
    log.info(f"found {len(nulls)} null geometries")
    if np.any(nulls):
        log.info("Found null entries")
        return data[data.geometry.values != None]  # remove null geometries
    else:
        return data


def remove_truly_duplicated_geometries(data: geopandas.GeoDataFrame):
    return data.drop_duplicates("geometry")


def mappy_construct(lines: geopandas.GeoDataFrame, points: geopandas.GeoDataFrame, output: str,
                    units_field: str, layer_name="geomap",
                    auto_extend=0, overwrite=False, debug=False):
    log.info("Executing mappy construct")
    log.info(f"CRS lines: {lines.crs}")
    log.info(f"CRS points: {points.crs}")

    out_args = {}
    out_args["layers"] = []

    if lines.crs != points.crs:
        log.warning("points and lines layers has different CRS, reprojecting...")
        points = points.to_crs(lines.crs)

    if os.path.exists(output):
        log.debug(f"File {output} exists!")
        existing_layers = fiona.listlayers(output)
        if layer_name in existing_layers and overwrite is not True:
            log.error(f"output geopackage {output} already contains a layer named {layer_name}.")
            return out_args

    if auto_extend != 0:
        log.info("extend_lines enabled, lines are extended")
        lines = extend_lines(lines, auto_extend)

        if debug:
            lines.to_file(output, layer="debug_extended_lines", driver="GPKG")
            out_args["layers"].append(lines)

    if debug:
        intersections = compute_self_intersections_points(lines)
        intersections.to_file(output, layer="debug_self_intersections", driver="GPKG")
        out_args["layers"].append("debug_self_intersections")

    polygons = polygonize(lines)

    if debug:
        polygons.to_file(output, layer="debug_polygons", driver="GPKG")
        out_args["layers"].append("debug_polygons")

    out = transfer_units_to_polygons(polygons, points, units_field)

    out.crs = None  # for now, then use the same as lines

    # from mappy.dev_tests import test_geopandas_save_gpkg
    # test_geopandas_save_gpkg()

    try:

        out.to_file(output, layer=layer_name, driver="GPKG")

    except Exception as e:
        print(e)
        raise e

    out_args["layers"].append(layer_name)
    out_args["gpkg"] = output

    return out_args


def mappy_deconstruct(polygons, units_field, output_gpkg, lines_layer_name, points_layer_name):
    log.info("Executing mappy deconstruct")
    lines, polygons = polygons_to_lines(polygons)  # it also returns a cleaned version of the polygonal layer
    points = generate_label_points(polygons)
    points = transfer_polygons_fields_to_points(points, polygons)
    points.reset_index()

    # points.crs = None

    lines.to_file(output_gpkg, layer=lines_layer_name, driver="GPKG")
    try:
        points.to_file(output_gpkg, layer=points_layer_name, driver="GPKG")
    except Exception as e:
        raise e
        # return points

    out_args = {}
    out_args["layers"] = []
    out_args["layers"].append(points)
    out_args["layers"].append(lines)

    return out_args


import topojson, copy
from topojson.ops import np_array_from_arcs


def extract_numpy_arcs(topology):
    t = None
    if "transform" in topology.output.keys():
        s = np.array(topology.output["transform"]["scale"])
        t = np.array(topology.output["transform"]["translate"])
    top = topology._resolve_coords(topology.output)
    np_arcs = np_array_from_arcs(top["arcs"])
    if t is not None:
        out = topojson.ops.dequantize(np_arcs, s, t)
    else:
        out = np_arcs

    out = [o[~np.isnan(o).any(axis=1)] for o in out]

    return out


from shapely.geometry import asLineString


def polygons_to_lines(polygons):
    polygons.geometry = polygons.buffer(0)
    polygons = explode_multipolygons(polygons)
    polygons = remove_null_geometries(polygons)
    polygons = remove_truly_duplicated_geometries(polygons)
    log.info(polygons)

    tj = topojson.Topology(polygons)

    out = extract_numpy_arcs(tj)

    glines = [asLineString(e) for e in out]
    asg = geopandas.GeoDataFrame(geometry=glines)
    return asg, polygons
