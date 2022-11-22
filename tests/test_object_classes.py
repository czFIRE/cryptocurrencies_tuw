from objects.Block import Block
from objects.Transaction import Transaction
from global_variables import DB_MANAGER

block_msg = {
    "type": "object",
    "object": {
        "type": "block",
        "txids": ["txid1"],
        "nonce": "my nonce",
        "previd": "my prev_id",
        "created": 1622825642,
        "T" : "my T", 
        "note" : "This is a note"
    }
}

transaction_msg = {
    "type":"transaction", 
    "height":128, 
    "outputs":[
        {
            "pubkey": "077a2683d776a71139fd4db4d00c16703ba0753fc8bdc4bd6fc56614e659cde3", 
            "value":50000000000
        } 
    ]
}


block = Block.load_from_json(block_msg["object"])

transaction = Transaction.load_from_json(transaction_msg)
print(transaction)
id_before = transaction.object_id

DB_MANAGER.add_object(transaction)
transaction = (DB_MANAGER.get_object(transaction.object_id))

print(id_before == transaction.object_id)

