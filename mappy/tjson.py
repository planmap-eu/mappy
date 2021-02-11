import frechetdist
import shapely
import topojson, copy
from matplotlib.pyplot import plot
from topojson.ops import np_array_from_arcs
import numpy as np
from typing import List

def extract_numpy_arcs(topology):
    t = False
    if "transform" in topology.output.keys():
        t = True
        s = np.array(topology.output["transform"]["scale"])
        t = np.array(topology.output["transform"]["translate"])
    top = topology._resolve_coords(topology.output)
    np_arcs = np_array_from_arcs(top["arcs"])
    if t is not False:
        out = topojson.ops.dequantize(np_arcs, s, t)
    else:
        out = np_arcs

    out = [o[~np.isnan(o).any(axis=1)] for o in out]

    return out





def reorder_points(points):
    startid = np.argmax(points[:, 1])
    ids = np.arange(len(points))
    if startid != 0:
        out = np.row_stack([points[startid:, :], points[1:startid, :], points[startid, :]])
        ids = np.concatenate([ids[startid:], ids[1:startid], [ids[startid]]])

        return out, ids
    else:
        return points, ids


import attr




@attr.attrs(eq=False)
class Arc:
    points = attr.ib(repr=False)
    real_points = attr.ib(repr=False)
    id = attr.ib()
    # separating_polygons = attr.ib(factory=list, repr=False)

    def __attrs_post_init__(self):
        if self.is_closed():
            self.real_points, ids = reorder_points(self.real_points)
            newpts = np.cumsum(self.points, axis=0)
            rearranged = newpts[ids]
            newpts = np.row_stack([rearranged[0], np.diff(rearranged, axis=0)])
            self.points = newpts

    def plot(self, *attrs, **kwattrs):
        plot(*np.cumsum(self.points, axis=0).T, *attrs, **kwattrs)

    def plot_real(self, *attrs, **kwattrs):
        plot(*self.real_points.T, *attrs, **kwattrs)

    def is_closed(self):
        if np.all(self.real_points[0] == self.real_points[-1]):
            return True
        else:
            return False

    def get_points(self, invert=False):
        if invert:
            return self.real_points[::-1]
        else:
            return self.real_points

    def get_start_point(self):
        return self.points[0]

    def get_end_point(self):
        return self.points[-1]

    def as_shapely(self, invert=False):
        return shapely.geometry.LineString(self.real_points)

    def equal(self, other, threshold=1e-3):
        if len(self.points) != len(other.points):
            return False

        if np.all(np.abs(self.real_points - other.real_points) < threshold):
            return True

        if np.all(np.abs(self.real_points - other.real_points[::-1]) < threshold):
            return True

        return False

    def distance_frechet(self, other):
        d = ff.distance(self.real_points, other.real_points)
        return d




@attr.attrs(eq=False, repr=False)
class DirectedArc():
    arc: Arc = attr.ib(default=None)
    direction: bool = attr.ib(default=True)

    def __repr__(self):

        sign = "+" if self.direction else "-"

        return f"{sign}DirArc_{self.arc.id}"


@attr.attrs(eq=False, repr=False)
class ArcLoop():
    arcs: List[DirectedArc] = attr.ib(factory=list)

    def __repr__(self):
        return self.arcs.__repr__()

    def __iter__(self):
        return self.arcs.__iter__()

    def __getitem__(self, item):
        return self.arcs.__getitem__(item)

    def get_undirected_arcs(self):
        out = set()
        for ar in self:
            out.add(ar.arc)

        return out




@attr.attrs(eq=False)
class Polygon():
    exterior: ArcLoop = attr.ib(default=None)
    interior: List[ArcLoop] = attr.ib(factory=list)

    def has_holes(self):
        return len(self.interior) > 0

    def get_number_of_holes(self):
        return len(self.interior)

@attr.attrs(eq=False)
class PolygonalTasselation():
    polygons: List[Polygon] = attr.ib(factory=list)

    def __iter__(self):
        return self.polygons.__iter__()

    def __getitem__(self, item):
        return self.polygons.__getitem__(item)

    def get_exterior_arcs(self):
        """only exterior arcs are returned"""
        out = set()

        for p in self:
            out = out.union(p.exterior.get_undirected_arcs())
        return out

    def get_all_arcs(self):
        ext = self.get_exterior_arcs()
        for p in self:
            for inner in p.interior:
                ext = ext.union(inner.get_undirected_arcs())

        return ext

@attr.attrs(eq=False)
class PolygonOld:
    arcs = attr.ib(factory=list, repr=True)

    def has_holes(self):
        if len(self.arcs) > 1:
            return True
        else:
            return False

    def as_shapely(self):
        ext_points = []
        for arc, order in self.arcs[0]:
            ext_points.append(arc.get_points(order))

        ext_points = np.row_stack(ext_points)

        inners = []
        for inner in self.arcs[1:]:
            ring = []
            for arc, order in inner:
                ring.append(arc.get_points(order))

            ring = np.row_stack(ring)
            inners.append(ring)

        pp = shapely.geometry.Polygon(ext_points, inners)
        return pp


def retrive_arcs_as_objects(polygon_ids, arcs):
    polygon_ids = np.array(polygon_ids)
    reverse = polygon_ids < 0

    polygon_ids[reverse] = -polygon_ids[reverse] - 1
    arcs = np.array(arcs)[polygon_ids]
    polarity = reverse

    return ArcLoop([DirectedArc(a, dir) for a, dir in zip(arcs, polarity)])

    # return np.column_stack([arcs, polarity])


def retrieve_arcs(tj):
    out = extract_numpy_arcs(tj)
    arcs = [Arc(points=np.array(arc_pts), real_points=real, id=id) for id, (arc_pts, real) in
            enumerate(zip(tj.output["arcs"], out))]
    return arcs


def retrieve_polygon(pol, arcs):
    out = []
    for arclist in pol["arcs"]:
        out.append(retrive_arcs_as_objects(arclist, arcs))

    p = Polygon(out[0], out[1:])
    # for l in out:
    #     for arc, order in l:
    #         if p not in arc.separating_polygons:
    #             arc.separating_polygons.append(p)
    return p


def retrieve_all_polygons(geometries, arcs):
    return [retrieve_polygon(g, arcs) for g in geometries.output["objects"]["data"]["geometries"]]

def topojson_to_objects(tj):
    arcs = retrieve_arcs(tj)
    pols = retrieve_all_polygons(tj, arcs)
    return PolygonalTasselation(pols)