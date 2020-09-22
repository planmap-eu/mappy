from .mappy_logging import logger as log

from .plotting import plot_contacts_and_units_points

from .geom_ops import extend_lines, compute_self_intersections_points, polygonize, transfer_units_to_polygons, \
    explode_multipolygons, transfer_polygons_fields_to_points, generate_label_points, remove_null_geometries, \
    remove_truly_duplicated_geometries

from .checks import check_validity_of_geometries

from .geom_ops import mappy_construct
