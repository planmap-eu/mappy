import geopandas
from matplotlib.pylab import grid, text, gca


def plot_contacts_and_units_points(contacts: geopandas.GeoDataFrame, units: geopandas.GeoDataFrame, units_field: str):
    """
    :param contacts:
    :param units:
    :param units_field:
    :return:
    """
    contacts.plot(color="black", ax=gca())
    units.plot(ax=gca(), edgecolor=None, column=units_field, markersize=80)
    data = units[["geometry", units_field]]
    for id, row in data.iterrows():
        text(row.geometry.x, row.geometry.y, row[units_field], fontsize=15)

    grid(True)
