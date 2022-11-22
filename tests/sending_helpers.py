import asyncio
import json
import time
from asyncio import StreamReader, StreamWriter

import constants
from constants import PORT
from message import msg_builder
from message.msg_handling import write_msg

RCV_TIMEOUT = 5


class SendingHelper:

    def __init__(self, test_ip):
        self.test_ip = test_ip

    async def _send_request_to_server(self, msg, writer, reader):
        data = msg_builder.serialize_msg(msg).encode() if msg and not isinstance(msg, bytes) else msg
        print(f"Sending {data}")
        writer.write(data)
        await writer.drain()
        received = b""
        start_time = time.time()
        while True:
            try:
                chunk = await asyncio.wait_for(reader.read(1000), RCV_TIMEOUT)
            except asyncio.TimeoutError:
                break
            received += chunk
            if not chunk or time.time() > start_time + 10:
                break
        received = received.decode()
        print(f"Received: {received}")
        return received

    async def send_request(self, messages: list[json], expected_responses: list[str], should_disconnect: bool = False):  # type: ignore
        assert len(messages) == len(expected_responses), "Must be same length"
        reader, writer = await asyncio.open_connection(self.test_ip, PORT)
        for msg, expected_response in zip(messages, expected_responses):
            received = await self._send_request_to_server(msg, writer, reader)
            assert expected_response in received, f"Response must contain {expected_response}"
        if should_disconnect:
            try:
                writer.write(msg_builder.serialize_msg(msg_builder.getpeers_msg()).encode())
                await writer.drain()
                received = await reader.read(100)
                assert not received
            except ConnectionError as e:
                print(f"Connection closed: {e}")
        writer.close()
        await writer.wait_closed()

    async def listen_server(self, expected_responses):
        print("Starting server")
        reader, writer = await asyncio.open_connection(self.test_ip, 18018)
        await self.handle_connection(reader, writer, expected_responses)

    async def handle_connection(self, reader: StreamReader, writer: StreamWriter, expected_responses):
        all_responses = []
        try:
            iterations = 1
            await write_msg(writer, msg_builder.hello_msg())
            await write_msg(writer, msg_builder.getpeers_msg())
            first_msg_str = await asyncio.wait_for(reader.readline(), timeout=1)
            print(f"Received message from peer {first_msg_str}")
            while True:
                try:
                    msg_bytes = await asyncio.wait_for(reader.readline(), 1)
                    print(f"Received message from peer {msg_bytes.decode()}")
                    all_responses.append(msg_bytes.decode())
                except:
                    pass
                await asyncio.sleep(1)
                iterations += 1
                if iterations > 10:
                    break
        except Exception as e:
            print(f"Exception: {e}")
        for expected_response in expected_responses:
            print(f"Expected Response: {expected_response}")
            assert expected_response in all_responses
