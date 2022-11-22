import json
import random
import time
import unittest

from message import msg_builder
import asyncio

from utils.json_builder import mk_canonical_json_str
from objects.Block import Block
from objects.Transaction import Transaction
from tests.sending_helpers import SendingHelper

pascal = "167.99.240.225"
tabea = "159.65.119.144"
christoph = "37.252.191.95"
bootstrap = "128.130.122.101"

# set ip for testing
sending_helper = SendingHelper("localhost")


class RequestTestStage1(unittest.TestCase):

    def test_receive_hello_on_connect(self):
        data = b""
        asyncio.run(sending_helper.send_request([data], ["hello"]))

    def test_receive_getpeers_on_connect(self):
        data = b""
        asyncio.run(sending_helper.send_request([data], ["getpeers"]))

    def test_message_order_error_must_close_socket(self):
        data = msg_builder.getpeers_msg()
        asyncio.run(sending_helper.send_request([data], ["error"], True))

    def test_hello_request(self):
        data = msg_builder.hello_msg()
        asyncio.run(sending_helper.send_request([data], ["hello"]))

    def test_hello_error_must_close_socket(self):
        data = msg_builder.hello_msg()
        data['version'] = "0.0.abc"
        asyncio.run(sending_helper.send_request([data], ["error"], True))

    def test_incomplete_hello(self):
        data = {"type": "hello"}
        asyncio.run(sending_helper.send_request([data], ["error"], True))

    def test_message_order_ok(self):
        data = [msg_builder.hello_msg(), msg_builder.getpeers_msg()]
        asyncio.run(sending_helper.send_request(data, ["hello", "peers"]))

    def test_receive_correct_peers_message(self):
        data = [msg_builder.hello_msg(), msg_builder.getpeers_msg(),
                {"peers": ["2.2.2.2:18018"], "type": "peers"}, msg_builder.getpeers_msg()]
        expected_responses = ["", "", "", "2.2.2.2:18018"]
        asyncio.run(sending_helper.send_request(data, expected_responses))

    def test_send_with_delay(self):
        msg_peers1 = b'{"type":"g'
        msg_peers2 = b'etpeers"}\n'
        data = [msg_builder.hello_msg(), msg_peers1, msg_peers2]
        expected_responses = ["hello", "", "peers"]
        asyncio.run(sending_helper.send_request(data, expected_responses))


class RequestTestStage2(unittest.TestCase):

    def test_transaction_message_building(self):
        tx1_msg: str = '{"object":{"height":0,"outputs":' \
                       '[{"pubkey":"8dbcd2401c89c04d6e53c81c90aa0b551cc8fc47c0469217c8f5cfbae1e911f9","value":50000000000}],' \
                       '"type":"transaction"},"type":"object"}\n'
        tx2: Transaction = Transaction(height=0, outputs=[
            {"pubkey": "8dbcd2401c89c04d6e53c81c90aa0b551cc8fc47c0469217c8f5cfbae1e911f9", "value": 50000000000}])
        tx2_msg = msg_builder.serialize_msg(msg_builder.object_msg(tx2))
        print(tx1_msg)
        print(tx2_msg)
        assert tx1_msg == tx2_msg

    def test_getobject_genesis(self):
        # gets the genesis block and verifies created field
        data = [msg_builder.hello_msg(),
                msg_builder.getobject_msg("00000000a420b7cefa2b7730243316921ed59ffe836e111ca3801f82a4f5360e")]
        expected_responses = ["hello", "1624219079"]
        asyncio.run(sending_helper.send_request(data, expected_responses))

    def test_object_hashing(self):
        # test hashing with genesis block as string
        ob_json: json = '{"T": "00000002af000000000000000000000000000000000000000000000000000000", ' \
                        '"created": 1624219079, "miner": "dionyziz", ' \
                        '"nonce": "0000000000000000000000000000000000000000000000000000002634878840", "note": "The Economist ' \
                        '2021-06-20: Crypto-miners are probably to blame for the graphics-chip shortage", "previd": null, ' \
                        '"txids": [], "type": "block"}'
        ob_class = Block.load_from_json(json.loads(ob_json))
        print(ob_class.object_id)
        assert ob_class.object_id == "00000000a420b7cefa2b7730243316921ed59ffe836e111ca3801f82a4f5360e"

    def test_send_transaction_request_object(self):
        # Send a new valid transaction object and then requests the same object, should receive the object.
        tx: Transaction = Transaction(height=0, outputs=[
            {"pubkey": "8dbcd2401c89c04d6e53c81c90aa0b551cc8fc47c0469217c8f5cfbae1e911f9", "value": 20}])
        data = [msg_builder.hello_msg(), msg_builder.object_msg(tx),
                msg_builder.getobject_msg(tx.object_id)]
        expected_responses = ["hello", "", mk_canonical_json_str(tx.to_json(tx))]
        asyncio.run(sending_helper.send_request(data, expected_responses))

    def test_other_peer_gets_same_object(self):
        # A sends a new valid transaction object and then B requests the same object, B should receive the object.
        tx: Transaction = Transaction(height=0, outputs=[
            {"pubkey": "8dbcd2401c89c04d6e53c81c90aa0b551cc8fc47c0469217c8f5cfbae1e911f9", "value": 20}])

        data = [msg_builder.hello_msg(), msg_builder.object_msg(tx)]
        expected_responses = ["hello", ""]
        asyncio.run(sending_helper.send_request(data, expected_responses))

        print("Starting second client...")
        data2: list[json] = [msg_builder.hello_msg(), msg_builder.getobject_msg(tx.object_id)]
        expected_responses2 = ["hello", mk_canonical_json_str(tx.to_json(tx))]
        asyncio.run(sending_helper.send_request(data2, expected_responses2))

    def test_receive_getobject(self):
        data = [msg_builder.hello_msg(),
                msg_builder.ihaveobject_msg("00000000a420b7cefa2b7730243316921ed59ffe836e111ca3801f82a4f11111")]
        expected_responses = ["hello", "getobject"]
        asyncio.run(sending_helper.send_request(data, expected_responses))

    def test_wrong_transaction_schema(self):
        tx: Transaction = Transaction.load_from_json({'height': -1, 'outputs': [{'pubkey': 'e5b5ed8d9f90bf6c865e76471e1ddb086a0bc0904dacc2938cfb7616b0e7a8f7', 'value': 50}], 'type': 'transaction'})
        data = [msg_builder.hello_msg(), msg_builder.object_msg(tx)]
        expected_responses = ["hello", "error"]
        asyncio.run(sending_helper.send_request(data, expected_responses))



class TwoClientTestsStage2(unittest.IsolatedAsyncioTestCase):

    async def test_must_send_ihaveobject(self):
        tx1: Transaction = Transaction.load_from_json({"height": 1, "outputs": [
        {"pubkey": "62b7c521cd9211579cf70fd4099315643767b96711febaa5c76dc3daf27c281c", "value": 50000000000000}],
            "type": "transaction"})
        tx2: Transaction = Transaction.load_from_json({"inputs": [
        {"outpoint": {"index": 0, "txid": "48c2ae2fbb4dead4bcc5801f6eaa9a350123a43750d22d05c53802b69c7cd9fb"},
         "sig": "d51e82d5c121c5db21c83404aaa3f591f2099bccf731208c4b0b676308be1f994882f9d991c0ebfd8fdecc90a4aec6165fc3440ade9c83b043cba95b2bba1d0a"}],
            "outputs": [{"pubkey": "228ee807767047682e9a556ad1ed78dff8d7edf4bc2a5f4fa02e4634cfcad7e0",
                         "value": 49000000000000}], "type": "transaction"})
        data2 = [msg_builder.hello_msg(), msg_builder.object_msg(tx1), msg_builder.object_msg(tx2)]
        expected_responses2 = ["hello", '{"objectid":"' + tx1.object_id + '","type":"ihaveobject"}\n', '{"objectid":"' + tx2.object_id + '","type":"ihaveobject"}\n']
        expected_responses1 = ['{"objectid":"' + tx1.object_id + '","type":"ihaveobject"}\n', '{"objectid":"' + tx2.object_id + '","type":"ihaveobject"}\n']

        t1 = asyncio.create_task(sending_helper.send_request(data2, expected_responses2))
        t2 = asyncio.create_task(sending_helper.listen_server(expected_responses1))


        await t1
        await t2


    async def test_must_not_gossip(self):
        tx: Transaction = Transaction.load_from_json({"inputs": [
            {"outpoint": {"index": 1, "txid": "f76875e504b72322063a0c5ddff2d1c91a82665b33070eba257737c43a4e428e"},
             "sig": "996fb8d366b066d129f6fb5ef14ccd9a882952c47d90e58bf5b7ff397d072a6ff905380afcc541d60f8382dc226de3f3ec09250e6894e1a67fb8317257c68e0f"}],
            "outputs": [{"pubkey": "bb2e6868eb399a530c2dbcde6727d8f4d7ccb052c7ed20488322ee5fef4c65e2", "value": 50}],
            "type": "transaction"})
        data = [msg_builder.hello_msg(), msg_builder.object_msg(tx)]
        expected_responses2 = ["hello", 'error']

        t1 = asyncio.create_task(sending_helper.send_request(data, expected_responses2))
        t2 = asyncio.create_task(sending_helper.listen_server([]))

        await t1
        await t2


if __name__ == '__main__':
    unittest.main()
