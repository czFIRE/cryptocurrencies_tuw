schema = {
    "type": "object",
    "properties": {
        "type": {
            "type": "string"
        },
        "objectid": {
            "type": "string", "pattern": "^[a-f0-9]{64}$"
        }
    },
    "required": ["type", "objectid"],
    "additionalProperties": False
}