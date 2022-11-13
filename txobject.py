from dataclasses import dataclass


@dataclass
class TxObject:
    type: str
    txids: list  # should be array
    nonce: str
    previd: str
    created: int
    T: str

@dataclass
class TransactionObject:
    type: str
    inputs: list
    outputs: list

@dataclass
class CoinbaseTransaction:
    type: str
    height: int
    outputs: list
