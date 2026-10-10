from gig import Ent, EntType

from DrivingTimeMap import DrivingTimeMap
from LatLng import LatLng


def main(ent_type, centroid_ent_id):
    ents = Ent.list_from_type(ent_type)
    ent_centroid = Ent.from_id(centroid_ent_id)
    centroid = LatLng.from_ent(ent_centroid)

    for ent in ents:
        latlng = LatLng.from_ent(ent)
        print(
            ent.id,
            ent.name,
            latlng,
            centroid.distance(latlng),
            centroid.driving_info(latlng),
        )

    image_path = f"driving_time-{centroid_ent_id}-{ent_type.name}.png"
    DrivingTimeMap(ent_centroid, ents).write(image_path)
    print(f"Wrote {image_path}")


if __name__ == "__main__":
    for ent_type, centroid_ent_id in [
        (EntType.PROVINCE, "LK-1"),
        (EntType.DISTRICT, "LK-11"),
        (EntType.DSD, "LK-1103"),
    ]:
        main(ent_type, centroid_ent_id)
