def test_geopandas_save_gpkg():
    import geopandas
    from shapely.geometry import LineString as Line

    l = Line([[0, 1], [1, 2]])
    df = geopandas.GeoDataFrame(geometry=[l])

    df.to_file("/home/luca/qua.gpkg", layer="name", driver="GPKG")

