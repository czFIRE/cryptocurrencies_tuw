import json
import unittest

from jsonschema.exceptions import ValidationError

import message.msg_validation
from utils.json_builder import mk_canonical_json_str
from message.msg_exceptions import InvalidMsgException
from objects.Transaction import Transaction
from objects.obj_validation import validate_object
from global_variables import DB_MANAGER

object_msg = {"type": "object"}

transactions: (bool, json) = [
    (True, {"height": 1, "outputs": [
        {"pubkey": "62b7c521cd9211579cf70fd4099315643767b96711febaa5c76dc3daf27c281c", "value": 50000000000000}],
            "type": "transaction"}),
    (True, {"inputs": [
        {"outpoint": {"index": 0, "txid": "48c2ae2fbb4dead4bcc5801f6eaa9a350123a43750d22d05c53802b69c7cd9fb"},
         "sig": "d51e82d5c121c5db21c83404aaa3f591f2099bccf731208c4b0b676308be1f994882f9d991c0ebfd8fdecc90a4aec6165fc3440ade9c83b043cba95b2bba1d0a"}],
            "outputs": [{"pubkey": "228ee807767047682e9a556ad1ed78dff8d7edf4bc2a5f4fa02e4634cfcad7e0",
                         "value": 49000000000000}], "type": "transaction"}),
    (True, {"height": 0,
            "outputs": [{"pubkey": "8bd22d5b544887762cd6104b433d93e1f9a5f451fe47d641733e517d9551ab05", "value": 50}],
            "type": "transaction"}),
    (False, {"inputs": [
        {"outpoint": {"index": 0, "txid": "29e793963f3933af943d20cb3b8da893488c2e4fd169d88fd47c8081a368794c"},
         "sig": "648d0db001fe44edda0493b9635a9747b5f1b7e4b90032c17a3abc2aa874f4e2a0090ad7f43d1ce22614a52f6a13797dc2908e602a1c46c8cf32ec2ad910600b"}],
             "outputs": [{"pubkey": "8bd22d5b544887762cd6104b433d93e1f9a5f451fe47d641733e517d9551ab05", "value": 51}],
             "type": "transaction"}),
    (True, {"height": 0,
            "outputs": [{"pubkey": "bb2e6868eb399a530c2dbcde6727d8f4d7ccb052c7ed20488322ee5fef4c65e2", "value": 50}],
            "type": "transaction"}),
    (False, {"inputs": [
        {"outpoint": {"index": 1, "txid": "f76875e504b72322063a0c5ddff2d1c91a82665b33070eba257737c43a4e428e"},
         "sig": "996fb8d366b066d129f6fb5ef14ccd9a882952c47d90e58bf5b7ff397d072a6ff905380afcc541d60f8382dc226de3f3ec09250e6894e1a67fb8317257c68e0f"}],
             "outputs": [{"pubkey": "bb2e6868eb399a530c2dbcde6727d8f4d7ccb052c7ed20488322ee5fef4c65e2", "value": 50}],
             "type": "transaction"}),
    (True, {"height": 0,
            "outputs": [{"pubkey": "7d1b8f51c35cb8ecddc8c671138499bc8f37421a8906becff5cd318cf088b041", "value": 50}],
            "type": "transaction"}),
    (False, {"inputs": [
        {"outpoint": {"index": 0, "txid": "79f9b136a706e2a82a44b18e8ddc7e2e67757ea942bd2851c09314f3ddcdbe19"},
         "sig": "44779f8ef39b5e0bfd0a197e17e9a6734c22a512c8d8dc9b4a39b4451b8af5bce08c91d9be849c8cb6c470362fad240b95c6378a875d81559d2291b372742f0f"}],
             "outputs": [], "type": "transaction"}),
    (False, {"inputs": [],
             "outputs": [{"pubkey": "15b487609105690349484d831c2d6ea33e96686be7801f5409659713cad62c20", "value": 0}],
             "type": "transaction"}),
    (True, {"height": 0,
            "outputs": [{"pubkey": "06abdd0a320df08c1e9d00e60c57409b1a6754428806a6d5d7f855885c48d540", "value": 50}],
            "type": "transaction"}),
    (True, {"height": 0,
            "outputs": [{"pubkey": "1d917705041ac7765510872543dee033fe5fe8a652854d7f3e62c65b538ad6aa", "value": 50}],
            "type": "transaction"}),
    (True, {"inputs": [
        {"outpoint": {"index": 0, "txid": "ce175f46aeca15cbb80b66d261519f223d992e23dd268721f4135b58f4497a2e"},
         "sig": "cbd77bf5cdb2a252aea728d776adab2029a2cc375def7f3196fe423111b9374a71cb6707bbfb3bf6833db4218426f8b9f32a5708cad36476decb6da565209d05"},
        {"outpoint": {"index": 0, "txid": "b5770e009b63dc8d9aa3334dfe913ac098738dc02e4b379f96e663ec86aa81eb"},
         "sig": "3833f90108952068758a30e287d026e7b74d844026333c904d62dd92351330002996e947c0178f9c2248a1dc1d711101df3a385af15e78afdacd723202f2be0c"}],
        "outputs": [{"pubkey": "06abdd0a320df08c1e9d00e60c57409b1a6754428806a6d5d7f855885c48d540", "value": 20}],
        "type": "transaction"}),
    (True, {"height": 0,
            "outputs": [{"pubkey": "5e3f197d8b63a853b79330d96a82d2ad51ff06605879f5f4b664c1d9a6b9c02e", "value": 50}],
            "type": "transaction"}),
    (True, {"inputs": [
        {"outpoint": {"index": 0, "txid": "8a6fdba6541db169d9bb3249e91bfde5692048818031aa55062a41c673bd01ea"},
         "sig": "6f3d4522bf29e55becb3ce707830f62954cb109464737ea37bd0213f14ea52b530fe0c13d56c9496fa72466cbd94fb0a927e53a57786bca2dfa7214c89580403"}],
        "outputs": [{"pubkey": "5e3f197d8b63a853b79330d96a82d2ad51ff06605879f5f4b664c1d9a6b9c02e", "value": 50}],
        "type": "transaction"}),
    # TODO: should be false
    (True, {"height": 0,
             "outputs": [{"pubkey": "94d9791bacecb33702a9914eb54881e9904e0dced984229e39746bfc32639546", "value": 50},
                         {"pubkey": "94d9791bacecb33702a9914eb54881e9904e0dced984229e39746bfc32639546", "value": 20}],
             "type": "transaction"}),
    (False, {"height": 0, "outputs": [], "type": "transaction"}),
    (False, {"height": 0,
             "outputs": [{"pubkey": "d78192f91c549f0e7e82fcdbb5227e81d75eff257e519decdcad80fea0036e17", "value": -50}],
             "type": "transaction"}),
    (False, {"height": -1,
             "outputs": [{"pubkey": "e5b5ed8d9f90bf6c865e76471e1ddb086a0bc0904dacc2938cfb7616b0e7a8f7", "value": 50}],
             "type": "transaction"}),
    (True, {"height": 0,
            "outputs": [{"pubkey": "57558a6dae91ac3ab8caf3f543eac9c51cba4ac680ba5ba0d81b5575dc06bc46", "value": 50}],
            "type": "transaction"}),
    (True, {"inputs": [
        {"outpoint": {"index": 0, "txid": "2fb7adb654b373e85c6b5c596cc110dcb6643ee138768f4aa947e9ddb7d91f8d"},
         "sig": "1bc4c05ec180932f08b95a8b5be308bb7b90c4d047720c4953440ea7cf56ba38b7e3b52ae586b594a6ae6649d8be0ae3d6944ffe9a7c5894622c33b9df276909"}],
            "outputs": [{"pubkey": "857debb2084fc8c87dec10d305993e781d9c9dbf6a81762b2f245095ae6b8fb9", "value": 50}],
            "type": "transaction"}),
    (True, {"inputs": [
        {"outpoint": {"index": 0, "txid": "8ba50dc37eeac718eb3c631dd0c928b473b81ae9a2f592b0302916610df9c28c"},
         "sig": "4dd5fdb7df361fa43fa38dd5aed595b09d8c5f3b71b6fe23cdbb9009aa251a1be4e179f37e5bafc8d67193f760f0eda7d0fda1e75a50e47d7727fec69ff0290e"}],
            "outputs": [{"pubkey": "857debb2084fc8c87dec10d305993e781d9c9dbf6a81762b2f245095ae6b8fb9", "value": 50}],
            "type": "transaction"}),
]



class MessageValidationTests(unittest.TestCase):
    def test_message_validation_schema_correct(self):
        for transaction in transactions:
            msg = build_object_msg(transaction[1])
            print(msg)
            try:
                msg_type, json_data = message.msg_validation.validate_message(json.dumps(msg).encode())
            except Exception:
                print(f"Wrong schema: {msg}")
                msg_type = None
            assert msg_type == "object" or transaction[0] is False


    def test_transaction_validation(self):
        for transaction in transactions:
            if transaction[0]:
                transaction_object = Transaction.load_from_json(transaction[1])
                DB_MANAGER.add_object(transaction_object)
        for transaction in transactions:
            msg = build_object_msg(transaction[1])
            try:
                msg_type, json_data = message.msg_validation.validate_message(json.dumps(msg).encode())
            except Exception as e:
                print(e)
                msg_type = None
            if msg_type == "object":
                transaction_object = Transaction.load_from_json(transaction[1])
                print(f"{transaction[0]}: {mk_canonical_json_str(transaction_object.to_json(transaction_object))}")
                assert validate_object(transaction_object) == transaction[0]


def build_object_msg(object_json: json):
    msg = object_msg
    msg["object"] = object_json
    return msg
