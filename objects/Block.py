import json

from objects.Object import Object


class Block(Object):
    def __init__(self, txids: list[str], nonce: str, previd: str, created: int, t: str, miner: str = "undefined",
                 note: str = None):
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
    def load_from_json(cls, json_data: json):
        miner = json_data["miner"] if "miner" in json_data else None
        note = json_data["note"] if "note" in json_data else None

        return cls(
            json_data["txids"],
            json_data["nonce"],
            json_data["previd"],
            json_data["created"],
            json_data["T"],
            miner,
            note
        )
