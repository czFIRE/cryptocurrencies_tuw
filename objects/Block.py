import json

from objects.Object import Object as Object_


class Block(Object_):
    def __init__(self, txids: list[str], nonce: str, previd: str, created: int, t: str, miner: str = "undefined",
                 note: "str|None" = None):
        super().__init__("block")

        self.txids = txids
        self.nonce = nonce
        self.previd = previd
        self.created = created
        self.T = t
        self.miner = miner
        self.note = note

        # Hash the whole instance and set its object_id
        self.generate_obj_id()

    @classmethod
    def load_from_json(cls, json_data: json):  # type: ignore
        miner = json_data["miner"] if "miner" in json_data else None  # type: ignore
        note = json_data["note"] if "note" in json_data else None  # type: ignore

        return cls(
            json_data["txids"],  # type: ignore
            json_data["nonce"],  # type: ignore
            json_data["previd"],  # type: ignore
            json_data["created"],  # type: ignore
            json_data["T"],  # type: ignore
            miner,  # type: ignore
            note
        )
