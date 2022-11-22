import constants as const
import json

from utils.json_builder import mk_canonical_json_str
from objects import Object
from peers.Peer import Peer


def error_msg(error_str) -> json:
    return {"type": "error", "error": error_str}


def hello_msg() -> json:
    return {
        "type": "hello",
        "version": const.VERSION,
        "agent": const.AGENT
    }


def getpeers_msg() -> json:
    return {
        "type": "getpeers"
    }


def peers_msg(peers: list[Peer]) -> (json, int):
    peers_str = [str(p) for p in peers]
    return {
        "type": "peers",
        "peers": peers_str
    }


def getobject_msg(object_id: str) -> json:
    return {
        "type": "getobject",
        "objectid": object_id
    }


def ihaveobject_msg(object_id: str) -> json:
    return {
        "type": "ihaveobject",
        "objectid": object_id
    }


def object_msg(app_obj: Object) -> json:
    return {
        "type": "object",
        "object": app_obj.to_json(app_obj)
    }


def serialize_msg(msg_dict: json) -> str:
    return f"{mk_canonical_json_str(msg_dict)}\n"
