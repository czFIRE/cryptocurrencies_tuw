from dataclasses import dataclass


@dataclass
class TxObject:
    type: str
    txids: any  # should be array
    nonce: str
    previd: str
    created: int
    T: str

@dataclass
class TransactionObject:
    type: str
    inputs: list  # should be array
    outputs: str
