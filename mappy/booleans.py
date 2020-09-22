import pyclipper
import shapely
import numpy as np

from collections import Sequence
from itertools import chain, count


def depth(seq):
    seq = iter(seq)
    try:
        for level in count():
            seq = chain([next(seq)], seq)
            seq = chain.from_iterable(s for s in seq if isinstance(s, Sequence))
    except StopIteration:
        return level


def shapely_to_clipper(polygon):
    ext = np.array(polygon.exterior.coords)
    ext = pyclipper.scale_to_clipper(ext)

    ints = [pyclipper.scale_to_clipper(np.array(inters.coords)) for inters in polygon.interiors]
    ints.insert(0, ext)
    return ints


def clipper_to_shapely(data):
    if depth(data) == 2:
        return shapely.geometry.Polygon(pyclipper.scale_from_clipper(data))
    else:

        ext = pyclipper.scale_from_clipper(data[0])
        ints = [pyclipper.scale_from_clipper(i) for i in data[1:]]

    return shapely.geometry.Polygon(ext, ints)


def add_paths(clip, subj):
    pc = pyclipper.Pyclipper()
    pc.Clear()
    if depth(clip) == 2:
        pc.AddPath(clip, pyclipper.PT_CLIP, True)
    else:
        pc.AddPaths(clip, pyclipper.PT_CLIP, True)

    if depth(subj) == 2:
        pc.AddPath(subj, pyclipper.PT_SUBJECT, True)
    else:
        pc.AddPaths(subj, pyclipper.PT_SUBJECT, True)

    return pc


def intersect(clip, subj):
    pc = add_paths(clip, subj)
    return pc.Execute(pyclipper.CT_INTERSECTION, pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD)


def union(clip, subj):
    pc = add_paths(clip, subj)
    return pc.Execute(pyclipper.CT_UNION, pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD)


def difference(clip, subj):
    pc = add_paths(clip, subj)
    return pc.Execute(pyclipper.CT_DIFFERENCE, pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD)


# solution (a list of paths): [[[240, 200], [190, 200], [190, 150], [240, 150]], [[200, 190], [230, 190], [215, 160]]]

def recompute_pols(p1, p2):
    p1p = shapely_to_clipper(p1)
    p2p = shapely_to_clipper(p2)

    inter = intersect(p1p, p2p)
    e = union(p1p, inter)
    e2 = difference(inter, p2p)

    a, b = clipper_to_shapely(e), clipper_to_shapely(e2)
    a = a.buffer(0)
    b = b.buffer(0)
    return a, b
