import re
import json

from typing import Type
from global_variables import DB_MANAGER
from objects.Transaction import Transaction
from objects.Block import Block
from objects.Object import Object
from utils.json_builder import mk_canonical_json_str
from nacl.encoding import HexEncoder
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError


def _validate_normal_transaction(tx: Transaction) -> bool:
    sum_inputs = 0
    # 2a) For each input, ...
    for input in tx.inputs:
        # 2a) ... ensure that a valid transaction with the given txid exists in your object database.
        prev_tx_str = DB_MANAGER.get_tx_obj(input["outpoint"]["txid"])
        if not prev_tx_str:
            return False

        # 2a) ... ensure that the given index is less than the number of outputs in the outpoint transaction.
        index = input["outpoint"]["index"]
        prev_tx = json.loads(prev_tx_str)

        if index >= len(prev_tx["outputs"]):
            return False

        output = prev_tx["outputs"][index]

        # 2b) ... verify the signature (ed25519)
        verify_key = VerifyKey(output["pubkey"], encoder=HexEncoder)
        signature_bytes = HexEncoder.decode(input["sig"])

        # Signatures are created on the plaintext which consists of the transaction they are contained within,
        # except that the sig values are all replaced with null.
        signed_bytes = re.sub(r'\"sig\":\"[0-9a-f]{128}\"', '"sig":null',
                              mk_canonical_json_str(Transaction.to_json(tx))).encode()

        try:
            verify_key.verify(signed_bytes, signature_bytes)
        except BadSignatureError:
            return False

        # 2d) Transactions must respect the law of conservation
        sum_inputs += output["value"]

    # 2d) Transactions must respect the law of conservation, i.e. the sum of all input values is at least
    # the sum of output values.
    sum_outputs = sum(output["value"] for output in tx.outputs)
    if sum_inputs < sum_outputs:
        return False

    # Transaction is valid!
    return True


def _validate_transaction(tx: Transaction) -> bool:
    if tx.height or tx.height == 0:
        # Coinbase Transaction
        # For now, assume that a coinbase transaction is always valid. We will validate these starting in the next
        # homework.
        return True

    # Normal Transaction
    return _validate_normal_transaction(tx)


def validate_object(obj: Type[Object]) -> bool:
    match obj:
        case Transaction():
            # noinspection PyTypeChecker
            return _validate_transaction(obj)
        case Block():
            # For this homework, you may consider blocks and coinbase transactions to always be valid.
            return True
