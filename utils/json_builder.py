import json


def mk_canonical_json_str(json_object: json) -> str:
    return json.dumps(json_object, sort_keys=True, separators=(',', ':'))
