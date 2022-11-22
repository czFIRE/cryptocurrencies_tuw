import asyncio
import logging as log
import time

import constants as const
import message.msg_builder as build

from asyncio import StreamWriter, StreamReader
from peers.Peer import Peer
from message.msg_handling import write_msg, handle_msg
from message.msg_validation import validate_message
from message.msg_exceptions import MessageException, UnexpectedMsgException, ErrorMsgException
from objects.obj_exceptions import ValidationException
from jsonschema import ValidationError
from json import JSONDecodeError
from global_variables import CONNECTIONS, DB_MANAGER


def add_connection(peer: Peer, writer: StreamWriter):
    CONNECTIONS[peer] = writer
    DB_MANAGER.add_peers([peer])


def del_connection(peer: Peer):
    writer = CONNECTIONS.pop(peer, None)
    if (writer is not None):
        writer.close()
    DB_MANAGER.remove_peer(peer)


async def listen():
    log.info(f"Starting server on port {const.PORT}")
    return await asyncio.start_server(handle_connection, const.HOST, const.PORT)


async def handle_connection(reader: StreamReader, writer: StreamWriter):
    peer_data = writer.get_extra_info('peername')
    peer = Peer(peer_data[0], peer_data[1])
    add_connection(peer, writer)

    msg = None
    msg_bytes = None

    try:
        # Initial Handshake
        await write_msg(writer, build.hello_msg())  # type: ignore
        await write_msg(writer, build.getpeers_msg())  # type: ignore

        first_msg_bytes = await asyncio.wait_for(reader.readline(), timeout=const.HELLO_MSG_TIMEOUT)
        log.info(f"Received message from peer {peer}")

        msg_type, first_msg = validate_message(first_msg_bytes)

        if not msg_type == 'hello':
            raise UnexpectedMsgException("First message needs to be of type 'hello'")

        # Listen for messages...
        while True:
            msg_bytes = await reader.readline()
            log.info(f"Received message from peer {peer}")

            msg_type, msg = validate_message(msg_bytes)
            await handle_msg(writer, msg_type, msg, peer)  # type: ignore

    except asyncio.exceptions.TimeoutError:
        log.info(f"Peer {peer} timed out...")
    except ErrorMsgException:
        tmp = "MSG is None" if msg is None else msg['error']  # type: ignore
        log.error(f"Received 'Error' message from peer {peer}. Error: {tmp}")
    except MessageException as e:
        log.info(f"Message from peer {peer} produced error. Error: {e}")
        log.debug(f'The message was: {msg}')
        try:
            log.debug(f"Sending 'Error' message to {peer}")
            await write_msg(writer, build.error_msg(str(e)))  # type: ignore
            log.info(f"'Error' message send to {peer}")
        except Exception as e:
            log.error(f"Could not send 'Error' message to {peer}. Error: {e}")
    except BrokenPipeError as e:
        log.info(f"Connection lost to {peer}. Error: {e}")
    except ValidationException as e:
        log.info(f"Object received from peer {peer} is invalid!")
        log.debug(f"The object was: {msg}")
        try:
            log.debug(f"Sending 'Error' message to {peer}")
            await write_msg(writer, build.error_msg(str(e)))  # type: ignore
            log.info(f"'Error' message send to {peer}")
        except Exception as e:
            log.error(f"Could not send 'Error' message to {peer}. Error: {e}")
    except JSONDecodeError as e:
        log.info(f"Message received from peer {peer} is not a valid JSON document!")
        log.debug(f"The message was: {msg_bytes}")
        try:
            log.debug(f"Sending 'Error' message to {peer}")
            await write_msg(writer, build.error_msg("Message is not a valid JSON document"))  # type: ignore
            log.info(f"'Error' message send to {peer}")
        except Exception as e:
            log.error(f"Could not send 'Error' message to {peer}. Error: {e}")
    except ValidationError or KeyError as e:
        log.info(f"Message received from peer {peer} is invalid!")
        log.debug(f"The message was: {msg_bytes}")
        try:
            log.debug(f"Sending 'Error' message to {peer}")
            await write_msg(writer, build.error_msg("Message is invalid"))  # type: ignore
            log.info(f"'Error' message send to {peer}")
        except Exception as e:
            log.error(f"Could not send 'Error' message to {peer}. Error: {e}")
    except ValueError as e:
        log.error(e)
    except Exception as e:
        log.error(e)
    finally:
        log.info(f"Closing connection with peer {peer}")
        del_connection(peer)


async def connect_to_node(peer: Peer):
    try:
        log.info(f"Connecting to {peer}...")
        reader, writer = await asyncio.open_connection(peer.host, peer.port)
    except Exception as e:
        log.error(f"Could not connect to peer {peer}. Error: {e}")
        return

    log.info(f"New connection with {peer}")
    await handle_connection(reader, writer)


async def bootstrap():
    for p in const.PRELOADED_PEERS:
        asyncio.create_task(connect_to_node(p))

    # Request Genesis Block
    while len(CONNECTIONS.items()) == 0:
        await asyncio.sleep(0.1)
    await write_msg(CONNECTIONS[const.BOOTSTRAP_NODE], build.getobject_msg(const.OBJECT_ID_GENESIS_BLOCK))  # type: ignore
    log.info("Requested Genesis Block from Bootstrap Node")


def resupply_connections(delta_peers: int):
    random_peers = [p for p in DB_MANAGER.get_random_peers(delta_peers) if p not in CONNECTIONS]

    if random_peers:
        log.info(f"Trying to connect to {len(random_peers)} new peers")

        for peer in random_peers:
            asyncio.create_task(connect_to_node(peer))
