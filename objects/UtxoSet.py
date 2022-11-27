import json
import os
import sys

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from utils.json_builder import mk_canonical_json_str


class UtxoSet:
    def __init__(self, set_id: "str|None" = None, balances: "list[str]|None" = None):
        self.set_id = set_id
        self.balances = balances

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
