import json
import os
import sys
import logging as log

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from utils.json_builder import mk_canonical_json_str


class UtxoSet:
    def __init__(self, set_id: str, state: "dict|None" = None):
        self.set_id = set_id
        self.state = state

    def __str__(self):
        return mk_canonical_json_str(self.__dict__)

    def __repr__(self):
        return self.__str__()

    # TODO: Make sure this actually works when things are None
    @staticmethod
    def to_json(obj) -> json:
        excluded_fields = ["set_id"]
        return {key: value for key, value in obj.__dict__.items()
                if ((value or value == 0) and key not in excluded_fields)}

    @classmethod
    def load_from_json(cls, json_data: json):
        log.debug(f"load_from_json: {json_data}")
        state = json_data["state"] if "state" in json_data else None
        return cls(
            state
        )
