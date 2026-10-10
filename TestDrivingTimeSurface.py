import unittest

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import GeometryCollection, LineString, Polygon

from DrivingTimeSurface import DrivingTimeSurface


class TestDrivingTimeSurface(unittest.TestCase):
    def test_invalid_geometry_supports_mask_and_clip(self):
        bowtie = Polygon([(0, 0), (2, 2), (0, 2), (2, 0), (0, 0)])
        square = Polygon([(0.5, 0), (1.5, 0), (1.5, 1), (0.5, 1)])
        gdf = gpd.GeoDataFrame(
            {
                "lng": [0, 1, 0],
                "lat": [0, 0, 1],
                "driving_time_hours": [0, 1, 2],
            },
            geometry=[bowtie, square, square],
        )
        surface = DrivingTimeSurface(gdf, resolution=20)
        self.assertTrue(surface.outline.is_valid)
        values = surface.values(*surface.grid())
        self.assertTrue(np.isfinite(values).any())
        fig, ax = plt.subplots()
        try:
            patch = surface.clip_patch(ax)
            self.assertGreater(len(patch.get_path().vertices), 0)
            fig.canvas.draw()
        finally:
            plt.close(fig)

    def test_valid_geometry_is_preserved(self):
        square = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        surface = DrivingTimeSurface(gpd.GeoDataFrame(geometry=[square]))
        self.assertTrue(surface.outline.equals(square))

    def test_geometry_collections_only_supply_polygons(self):
        square = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        collection = GeometryCollection(
            [GeometryCollection([square]), LineString([(0, 0), (2, 2)])]
        )
        self.assertEqual(
            DrivingTimeSurface.iter_polygons(collection), [square]
        )
