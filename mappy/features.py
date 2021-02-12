from enum import Enum

from importlib import __import__ as doimport

from mappy import log

# helper methods to determine features availability on the running platform.
# features determination is done at import time and cannot change during runtime, for now


class OptionalModules(Enum):
    geopandas = 0
    topojson = 1


class FeatureSet(Enum):
    geopandas_extended = 0
    pyqgis_only = 1



def test_modules():
    available_modules = []

    for a in OptionalModules:

        log.debug (f"testing import {a.name}")

        try:
            doimport(a.name)
            available_modules.append(a)
        except:
            log.warning("cannot import")
    return available_modules

def compute_feature_set(available_modules):
    if OptionalModules.geopandas in available_modules and OptionalModules.topojson in available_modules:
        return FeatureSet.geopandas_extended
    else:
        return FeatureSet.pyqgis_only

def determine_feauture_set():
    av_mods = test_modules()
    return compute_feature_set(av_mods)

features_set = determine_feauture_set()

