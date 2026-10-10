import numpy as np
import shapely
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from scipy.interpolate import RBFInterpolator


class DrivingTimeSurface:
    def __init__(self, gdf, resolution=400):
        self.gdf = gdf
        self.resolution = resolution
        self.outline = gdf.geometry.make_valid().union_all()

    def grid(self):
        min_x, min_y, max_x, max_y = self.gdf.total_bounds
        xs = np.linspace(min_x, max_x, self.resolution)
        ys = np.linspace(min_y, max_y, self.resolution)
        return np.meshgrid(xs, ys)

    def values(self, grid_x, grid_y):
        points = np.column_stack([self.gdf["lng"], self.gdf["lat"]])
        interpolator = RBFInterpolator(
            points,
            self.gdf["driving_time_hours"].to_numpy(),
            kernel="thin_plate_spline",
            smoothing=0.5,
        )
        grid_points = np.column_stack([grid_x.ravel(), grid_y.ravel()])
        values = interpolator(grid_points).reshape(grid_x.shape)
        land = shapely.contains_xy(self.outline.buffer(0.02), grid_x, grid_y)
        return np.where(land, np.clip(values, 0, None), np.nan)

    def clip_patch(self, ax):
        vertices, codes = [], []
        for polygon in self.iter_polygons(self.outline):
            for ring in [polygon.exterior, *polygon.interiors]:
                coords = list(ring.coords)
                vertices.extend(coords)
                codes.extend(
                    [Path.MOVETO]
                    + [Path.LINETO] * (len(coords) - 2)
                    + [Path.CLOSEPOLY]
                )
        patch = PathPatch(
            Path(vertices, codes), transform=ax.transData, fill=False
        )
        ax.add_patch(patch)
        return patch

    @classmethod
    def iter_polygons(cls, geometry):
        if geometry.geom_type == "Polygon":
            return [geometry]
        if geometry.geom_type in ("MultiPolygon", "GeometryCollection"):
            return [
                polygon
                for part in geometry.geoms
                for polygon in cls.iter_polygons(part)
            ]
        return []
