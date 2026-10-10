import fcntl
import json
import os
from dataclasses import dataclass
from math import atan2, cos, radians, sin, sqrt
from pathlib import Path
from urllib.request import urlopen


@dataclass(frozen=True)
class LatLng:
    lat: float
    lng: float

    def __post_init__(self):
        object.__setattr__(self, "lat", round(self.lat, 4))
        object.__setattr__(self, "lng", round(self.lng, 4))

    def distance(self, other):
        other = self.from_value(other)
        lat0, lng0 = radians(self.lat), radians(self.lng)
        lat, lng = radians(other.lat), radians(other.lng)
        dlat, dlng = lat - lat0, lng - lng0
        a = sin(dlat / 2) ** 2 + cos(lat0) * cos(lat) * sin(dlng / 2) ** 2
        return 6371 * 2 * atan2(sqrt(a), sqrt(1 - a))

    @classmethod
    def from_ent(cls, ent):
        return cls(ent.d["center_lat"], ent.d["center_lng"])

    @classmethod
    def from_value(cls, latlng):
        if isinstance(latlng, cls):
            return latlng
        return cls(*latlng)

    def driving_info(self, other):
        return self._get_driving_info(self.from_value(other))

    def _get_driving_info(self, other):
        cache_dir = Path("/tmp/cmb_distance")
        cache_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        cache_path = cache_dir / "driving_info_cache.json"
        lock_path = cache_dir / "driving_info_cache.lock"

        with lock_path.open("a") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            cache = self._read_cache(cache_path)
            key = f"{self.lng},{self.lat};{other.lng},{other.lat}"
            if key not in cache:
                cache[key] = self._request_driving_info(other)
                self._write_cache(cache, cache_path)
            return cache[key]

    @staticmethod
    def _read_cache(cache_path):
        if not cache_path.exists():
            return {}
        with cache_path.open(encoding="utf-8") as cache_file:
            cache = json.load(cache_file)
        if not isinstance(cache, dict):
            raise ValueError(f"Invalid OSRM cache format: {cache_path}")
        return cache

    @staticmethod
    def _write_cache(cache, cache_path):
        temporary_path = cache_path.with_suffix(".tmp")
        with temporary_path.open("w", encoding="utf-8") as cache_file:
            json.dump(cache, cache_file)
            cache_file.flush()
            os.fsync(cache_file.fileno())
        os.replace(temporary_path, cache_path)

    def _request_driving_info(self, other):
        url = (
            "https://router.project-osrm.org/route/v1/driving/"
            f"{self.lng},{self.lat};{other.lng},{other.lat}?overview=false"
        )
        with urlopen(url, timeout=30) as response:
            result = json.load(response)
        if result["code"] != "Ok":
            raise RuntimeError(result.get("message", result["code"]))
        routes = result["routes"]
        if not routes:
            raise RuntimeError("OSRM returned no driving route")
        route = routes[0]
        return {
            "driving_distance": route["distance"],
            "driving_time": route["duration"],
        }
