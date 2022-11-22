schema = {
    "type": "object",
    "properties": {
        "type": {
            "type": "string"
        },
        "peers": {
            "type": "array",
            "items": {
                "anyOf": [
                    {"type": "string", "format": "^\w+\.\w+\.[a-z]+\:\d+$"},     # Hostnames
                    {"type": "string", "pattern": "^\d+\.\d+\.\d+\.\d+\:\d+$"}   # IPv4
                ]
            }
        }
    },
    "required": ["type", "peers"],
    "additionalProperties": False
}