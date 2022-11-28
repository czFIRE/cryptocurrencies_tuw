import asyncio
import copy
import json
import logging as log
import re
from asyncio import StreamWriter
from typing import Type

from nacl.encoding import HexEncoder
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

import message.msg_builder as build
from constants import BLOCK_TARGET, TRANSACTIONS_ASKING_TIMEOUT
from global_variables import CONNECTIONS, DB_MANAGER
from message.msg_builder import serialize_msg
from objects.Block import Block
from objects.Object import Object
from objects.Transaction import Transaction
from utils.json_builder import mk_canonical_json_str
import time

from peers.Peer import Peer


# current_block_transactions: dict[Peer,list[str]] = {}
# current_block_transactions: tuple[int, Block] = (0, Block([], "", "", 0, ""))

async def write_msg(writer: StreamWriter, msg_dict: json):  # function copied from message.msg_handling.py
    msg_str = serialize_msg(msg_dict)
    writer.write(msg_str.encode("utf-8"))
    await writer.drain()


async def _validate_normal_transaction(tx: Transaction) -> bool:
    sum_inputs = 0
    # 2a) For each input, ...
    for input in tx.inputs:
        # 2a) ... ensure that a valid transaction with the given txid exists in your object database.
        tx_id: str = input["outpoint"]["txid"]
        
        prev_tx_str = DB_MANAGER.get_tx_obj(tx_id)
        if not prev_tx_str:
            await request_missing_txs([tx_id])
            await asyncio.sleep(TRANSACTIONS_ASKING_TIMEOUT)
            prev_tx_str = DB_MANAGER.get_tx_obj(input["outpoint"]["txid"])
            if not prev_tx_str:
                log.error(f"The transaction {tx_id} is missing in our DB!")
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


def is_coinbase(tx: Transaction) -> bool:
    return tx.height is not None and tx.inputs is None


async def _validate_transaction(tx: Transaction, peer: Peer) -> bool:
    if is_coinbase(tx):
        # Coinbase Transaction
        # For now, assume that a coinbase transaction is always valid. We will validate these starting in the next
        # homework.

        """
        current_context = copy.deepcopy(current_block_transactions)  # to atleast fix it for this checking - it can change

        if (peer in current_context):           # do we have anything from this peer in the storage?
            txids = current_context[peer]       # just pickout the txids stored
            if (tx in txids):                   # is the transaction in the storage even?
                if (len(are_missing_txs(txids)) > 0):       # do we have all transactions already
                    await asyncio.sleep(TRANSACTIONS_ASKING_TIMEOUT)                  # bit of sleep to allow fetching
                    if (len(are_missing_txs(txids)) > 0):                             # if we don't have everything
                        return False

                return await validate_coinbase_transactions(txids) # TODO - what to add here?!?!?!?!?!?!?!?!?!?!??!?!?! Does this work?!?! - should now, but still scatchy 
        """
        log.debug("Coinbase transaction received")
        return True  # we can't check it's validity

    # Normal Transaction
    return await _validate_normal_transaction(tx)


def are_missing_txs(txids: list[str]) -> list[str]:
    missing_txs: list[str] = []

    for tx in txids:
        if DB_MANAGER.get_tx_obj(tx) is None:
            missing_txs.append(tx)

    return missing_txs


async def request_missing_txs(txids: list[str]):
    for tx in txids:
        if DB_MANAGER.get_tx_obj(tx) is None:
            log.info(f"Requesting missing transaction {tx} from peers {list(CONNECTIONS.keys())}")
            for writer in CONNECTIONS.values():
                await write_msg(writer, build.getobject_msg(tx))


async def validate_coinbase_transactions(txids: list[str]) -> bool:
    """ Check if the block has only one coinbase transaction and if so, if the rules for coinbase transactions apply """

    log.debug("Validate Coinbase transactions")

    first = DB_MANAGER.get_tx_obj(txids[0])
    log.debug(f"Loaded first tx: {first}")
    first_tx = Transaction.load_from_json(json.loads(first))

    # Loop through all other transactions
    log.debug("Checking other transactions")
    for tx in txids[1:]:
        tmp = Transaction.load_from_json(json.loads(DB_MANAGER.get_tx_obj(tx)))

        # Only first transaction in list is allowed to be coinbase transaction
        if is_coinbase(tmp):
            return False

        # Output if coinbase transaction must not be used in other transactions in the same block
        for tx_input in tmp.inputs:
            # Input of transaction is output of coinbase transaction
            if is_coinbase(first_tx) and tx_input["outpoint"]["txid"] == txids[0]:
                return False

    # Rules for coinbase transactions must be satisfied
    log.debug("Check rules for coinbase transactions")
    if is_coinbase(first_tx):
        log.debug("Calculate transaction fee for coinbase transaction")
        fee = await calculate_transaction_fees(txids)
        if not await validate_coinbase_transaction(first_tx, fee):
            return False

    return True


async def calculate_transaction_fees(txids: list[str]) -> int:
    """ Calculate the transactions fees by subtracting the output sum from the input sum """

    if txids is None:
        log.debug("No transactions present: calculated fee is 0")
        return 0

    inputs = 0
    outputs = 0

    for tx in txids:
        log.debug(f"Adding transaction {tx} to output/input sum")
        tmp = Transaction.load_from_json(json.loads(DB_MANAGER.get_tx_obj(tx)))

        outputs += get_output_sum(tmp)
        inputs += get_input_sum(tmp)

    return inputs - outputs


def get_output_sum(transaction: Transaction) -> int:
    """ Calculate the output sum for a transaction"""

    if transaction.outputs is None:
        return 0

    output_value = 0
    for out in transaction.outputs:
        output_value += out["value"]

    return output_value


def get_input_sum(transaction: Transaction) -> int:
    """ Calculate the input sum of a transaction by looking at the outputs of all referenced input transactions """

    if transaction.inputs is None:
        return 0

    input_sum = 0
    for tx_input in transaction.inputs:
        input_id = tx_input["outpoint"]["txid"]
        # TODO do we have all of these transactions?
        tmp = Transaction.load_from_json(json.loads(DB_MANAGER.get_tx_obj(input_id)))
        log.debug("Getting output index")
        output_index = int(tx_input["outpoint"]["index"])
        log.debug(f"Output index is {output_index}")
        input_sum += tmp.outputs[output_index]["value"]
        log.debug(f"New input sum is {input_sum}")

    return input_sum


async def validate_coinbase_transaction(transaction: Transaction, fee: int) -> bool:
    """ Check if a coinbase transaction satisfies all criteria """

    log.debug("validate coinbase transaction")

    # coinbase transaction has no inputs
    if transaction.inputs is not None:
        log.debug("Coinbase transaction had inputs")
        return False

    # coinbase transaction has exactly one output
    if transaction.outputs is None or len(transaction.outputs) != 1:
        log.debug("Coinbase transaction had no outputs")
        return False

    # coinbase transaction has a height
    if transaction.height is None:  # this is redundant - already check in is_coinbase
        log.debug("Coinbase transaction had no height")
        return False

    # The output of the coinbase transaction can be at most the sum of transaction fees in the block plus the
    # block reward 50*10^12
    fee = fee + 50 * pow(10, 12)
    output_value = get_output_sum(transaction)
    if output_value > fee:
        log.debug(f"Coinbase transaction output sum {output_value} is greater than fee {fee}")
        return False

    log.debug("Coinbase transaction successfully validated")
    return True

async def _validate_block(block: Block, peer: Peer) -> bool:
    # check that the target is the one required
    if block.T != BLOCK_TARGET:
        log.error(
            f"Block target was {block.T} but expected {BLOCK_TARGET}")
        return False

    # TODO: reactivate this with a correct working version
    # check proof of work - this should work since we are converting both to int
    if int(block.T, base=16) <= block.__hash__():  # need to compare to the max number in target size - Do we?
        log.error(f"Block hash {block.__hash__()} is bigger than target {int(block.T, base=16)}!")
        return False

    if block.created > time.time() or block.created < 1624219079:   # TODO - we should be checking here for block.previd.created instead of this magical constant
        log.error(f"Block creation time {block.created} is in the future (current time {time.time()})")
        return False

    if len(block.txids) == 0:
        return True

    # Check if we are missing some transactions and request them if so
    missing_tx_ids = are_missing_txs(reversed(block.txids))
    orig_missing_tx_ids = copy.deepcopy(missing_tx_ids)

    """
    global current_block_transactions
    current_block_transactions[peer] = block.txids # TODO - this will break if we receive more block objects at the same time => we can solve this by technically creating a thread that will remember that for this instance 
                                                   # atleast now it doesn't break for multiple peers, but still breaks if the one sent us more objects at the same time
    """

    if len(missing_tx_ids) > 0:
        log.debug(f"Waiting for {missing_tx_ids} missing transactions")
        await request_missing_txs(missing_tx_ids)

    # TODO check if this is enough or this may still be too high? - ask on forums
    start_time = time.time()
    while time.time() - start_time < TRANSACTIONS_ASKING_TIMEOUT and len(missing_tx_ids) > 0:
        await asyncio.sleep(0.5)
        missing_tx_ids = are_missing_txs(orig_missing_tx_ids)  # can be optimalised by using missing_tx_ids

    missing_tx_ids = are_missing_txs(orig_missing_tx_ids)  # can be optimalised by using missing_tx_ids
    if len(missing_tx_ids) > 0:
        log.error(f"{len(missing_tx_ids)} transaction(s) couldn't be found!")
        # for tx in orig_missing_tx_ids:
        #    DB_MANAGER.remove_tx_obj(tx)
        return False

    log.debug("All transactions for block are here")

    # still needed if we already had the coinbase transaction in our DB 
    if not await validate_coinbase_transactions(block.txids):
        return False

    return True


async def validate_object(obj: Type[Object], peer: Peer = Peer("",0)) -> bool:
    match obj:
        case Transaction():
            # noinspection PyTypeChecker
            log.debug("Validating transaction")
            return await _validate_transaction(obj, peer)
        case Block():
            log.debug("Validating block")
            return await _validate_block(obj, peer)

    return False


