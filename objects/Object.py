import hashlib
import json

from utils.json_builder import mk_canonical_json_str


class Object:
    def __init__(self, type: str):
        self.type = type
        self.object_id = None

    def __str__(self):
        return mk_canonical_json_str(self.__dict__)

    def __repr__(self):
        return self.__str__()

    def generate_obj_id(self):
        json_str = mk_canonical_json_str(Object.to_json(self))
        self.object_id = hashlib.sha256(json_str.encode()).hexdigest()

    # removes None variables from JSON (maybe check if always filtering correctly)
    @staticmethod
    def to_json(obj) -> json:
        excluded_fields = ["object_id"]
        included_fields = ["previd", "txids"]
        return {key: value for key, value in obj.__dict__.items()
                if ((value or value == 0) and key not in excluded_fields)
                or key in included_fields}
