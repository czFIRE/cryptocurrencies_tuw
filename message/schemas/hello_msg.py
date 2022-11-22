schema = {
    "type": "object",
    "properties": {
        "type": {
            "type": "string"
        },
        "version": {
            "type": "string",
            "pattern": "^0\\.8\\.\\d+$"
        },
        "agent": {
            "type": "string"
        }
    },
    "required": ["type", "version", "agent"],
    "additionalProperties": False
}