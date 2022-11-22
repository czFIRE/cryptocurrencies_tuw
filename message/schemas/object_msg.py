schema = {
    "type": "object",
    "properties": {
        "type": {
            "type": "string"
        },
        "object": {
            "anyOf": [
                {"$ref": "#/$defs/transaction"},
                {"$ref": "#/$defs/block"}
            ]
        }
    },
    "required": ["type", "object"],
    "additionalProperties": False,

    "$defs": {
        "transaction": {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string"
                },
                "height": {
                    "type": "integer",
                    "minimum": 0
                },
                "inputs": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "properties": {
                            "outpoint": {
                                "type": "object",
                                "properties": {
                                    "txid": {
                                        "type": "string", "pattern": "^[a-f0-9]{64}$"
                                    },
                                    "index": {
                                        "type": "integer",
                                        "minimum": 0
                                    }
                                },
                                "required": ["txid", "index"],
                                "additionalProperties": False
                            },
                            "sig": {
                                "type": "string"
                            }
                        },
                        "required": ["outpoint", "sig"],
                        "additionalProperties": False
                    }
                },
                "outputs": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "properties": {
                            "pubkey": {
                                "type": "string", "pattern": "^[a-f0-9]{64}$"
                            },
                            "value": {
                                "type": "integer",
                                "minimum": 0
                            }
                        },
                        "required": ["pubkey", "value"],
                        "additionalProperties": False
                    }
                }
            },
            "oneOf": [
                {"required": ["type", "inputs", "outputs"]},
                {"required": ["type", "height", "outputs"]}
            ],
            "additionalProperties": False
        },
        "block": {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string"
                },
                "txids": {
                    "type": "array",
                    "items": {
                        "type": "string", "pattern": "^[a-f0-9]{64}$"
                    }
                },
                "nonce": {
                    "type": "string", "pattern": "^[a-f0-9]{64}$"
                },
                "previd": {
                    "anyOf": [
                        {"type": "string", "pattern": "^[a-f0-9]{64}$"},
                        {"type": "null"}
                    ]
                },
                "created": {
                    "type": "integer"
                },
                "T": {
                    "type": "string", "pattern": "^[a-f0-9]{64}$"
                },
                "note": {
                    "type": "string",
                    "maxLength": 128
                },
                "miner": {
                    "type": "string",
                    "maxLength": 128
                }
            },
            "required": ["type", "txids", "nonce", "previd", "created", "T"],
            "additionalProperties": False
        }
    }
}