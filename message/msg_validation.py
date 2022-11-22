import json
import jsonschema
import logging as log

from message.msg_exceptions import InvalidMsgException, MalformedMsgException
from message.schemas import hello_msg, getpeers_msg, peers_msg, object_msg, getobject_msg, ihaveobject_msg


def validate_message_schema(msg: json):  # type: ignore
    try:
        match msg['type']:  # type: ignore
            case 'hello':
                jsonschema.validate(msg, schema=hello_msg.schema)
            case 'getpeers':
                jsonschema.validate(msg, schema=getpeers_msg.schema)
            case 'peers':
                jsonschema.validate(msg, schema=peers_msg.schema)
            case 'object':
                jsonschema.validate(msg, schema=object_msg.schema)
            case 'ihaveobject':
                jsonschema.validate(msg, schema=ihaveobject_msg.schema)
            case 'getobject':
                jsonschema.validate(msg, schema=getobject_msg.schema)
            case 'getchaintip':
                pass
            case 'getmempool':
                pass
            case _:
                raise jsonschema.ValidationError('Unknown message type')
        return msg['type']  # type: ignore
    except jsonschema.SchemaError as error:
        log.error(f'Could not validate: Schema {error.schema} is invalid!')


def validate_message(msg: bytes) -> tuple[str, json]:  # type: ignore
    json_data = json.loads(msg)
    msg_type = validate_message_schema(json_data)

    return msg_type, json_data  # type: ignore
