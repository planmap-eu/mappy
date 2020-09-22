# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: all
#     notebook_metadata_filter: all,-language_info
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.5.2
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %%
# %pylab inline
import sys
sys.path.append("../")

import mappy, geopandas

from mappy.plotting import plot_contacts_and_units_points

# %%
lines = geopandas.read_file("../input_data/contacts")
lines = mappy.geom_ops.remove_null_geometries(lines)

points = geopandas.read_file("../input_data/unit_id")

attribute = "unit_name" # identifier for the units in the units point file

# %%
plot_contacts_and_units_points(lines, points, attribute)

# %%
out = mappy.geom_ops.mappy_construct(lines, points, "constructed.gpkg", attribute)

# %%
polygons = geopandas.read_file("constructed.gpkg")
polygons.plot(column="unit_name")

# %%
## now we test the deconstruction
out = mappy.geom_ops.mappy_deconstruct(polygons, "unit_name", "deconstucted.gpkg", "lines", "indicator_points")

# %%
dec_lines = geopandas.read_file("deconstucted.gpkg", layer="lines")
dec_points = geopandas.read_file("deconstucted.gpkg", layer="indicator_points")

# %%
plot_contacts_and_units_points(dec_lines, dec_points, attribute)

# %%

# %%
