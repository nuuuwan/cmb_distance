import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from gig import Ent, EntType

from DrivingTimeSurface import DrivingTimeSurface
from LatLng import LatLng


class DrivingTimeMap:
    def __init__(self, ent_centroid, ents):
        self.ent_centroid = ent_centroid
        self.ents = ents

    def build_gdf(self):
        centroid = LatLng.from_ent(self.ent_centroid)
        gdfs = []
        for ent in self.ents:
            gdf = ent.geo()
            latlng = LatLng.from_ent(ent)
            info = centroid.driving_info(latlng)
            gdf["name"] = ent.name
            gdf["lat"], gdf["lng"] = latlng.lat, latlng.lng
            gdf["driving_time_hours"] = info["driving_time"] / 3600
            gdfs.append(gdf)
        return gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))

    def draw_surface(self, ax, surface):
        grid_x, grid_y = surface.grid()
        values = surface.values(grid_x, grid_y)
        levels = np.arange(0, np.ceil(np.nanmax(values)) + 0.25, 0.25)
        filled = ax.contourf(
            grid_x, grid_y, values, levels=levels, cmap="turbo"
        )
        lines = ax.contour(
            grid_x,
            grid_y,
            values,
            levels=np.arange(1, np.ceil(np.nanmax(values)) + 1),
            colors="black",
            linewidths=0.6,
        )
        ax.clabel(lines, fmt="%dh", fontsize=7)
        patch = surface.clip_patch(ax)
        filled.set_clip_path(patch)
        lines.set_clip_path(patch)
        return filled

    @staticmethod
    def draw_district_boundaries(ax, crs):
        districts = Ent.list_from_type(EntType.DISTRICT)
        gdf = gpd.GeoDataFrame(
            pd.concat([ent.geo() for ent in districts], ignore_index=True)
        ).to_crs(crs)
        gdf.geometry = gdf.geometry.make_valid()
        gdf.boundary.plot(ax=ax, color="white", linewidth=0.4, alpha=0.7)

    def write(self, image_path):
        gdf = self.build_gdf()
        fig, ax = plt.subplots(figsize=(10, 10))
        filled = self.draw_surface(ax, DrivingTimeSurface(gdf))
        self.draw_district_boundaries(ax, gdf.crs)
        fig.colorbar(filled, ax=ax, label="Driving time (hours)", shrink=0.7)
        ax.set_title(f"Driving time from {self.ent_centroid.name}")
        ax.set_aspect("equal")
        ax.set_axis_off()
        plt.savefig(image_path, dpi=300)
        plt.close()
