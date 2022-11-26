import json

def mk_canonical_json_str(json_object: json) -> str:  # type: ignore
    return json.dumps(json_object, sort_keys=True, separators=(',', ':'))
