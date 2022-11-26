import hashlib
import json

import os, sys

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from utils.json_builder import mk_canonical_json_str

from jcs import canonicalize
from typing import Dict, Any

class Object:
    def __init__(self, type: str, object_id: "str|None" = None):
        self.type = type
        self.object_id = object_id

    def __str__(self):
        return mk_canonical_json_str(self.__dict__)  # type: ignore

    def __repr__(self):
        return self.__str__()

    def generate_obj_id(self):
        json_str = mk_canonical_json_str(Object.to_json(self))  # type: ignore
        self.object_id = hashlib.sha256(json_str.encode()).hexdigest()

    # removes None variables from JSON (maybe check if always filtering correctly)
    
    # TODO: Make sure this actually works when things are None  
    @staticmethod
    def to_json(obj) -> json:  # type: ignore
        excluded_fields = ["object_id"]
        included_fields = ["previd", "txids"]
        return {key: value for key, value in obj.__dict__.items()  # type: ignore
                if ((value or value == 0) and key not in excluded_fields)
                or key in included_fields}

    def __hash__(self) -> int:
        return int(self.sha256(), base=16)

    def asdict(self) -> Dict[str, Any]:
        return self.__dict__

    def sha256(self) -> str:
        json_str = mk_canonical_json_str(Object.to_json(self))  # type: ignore
        return hashlib.sha256(json_str.encode()).hexdigest()
