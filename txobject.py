from dataclasses import dataclass
from typing import Any, List

@dataclass
class BlockObject:
    type: str
    txids: List[Any] # should be array
    nonce: str
    previd: str
    created: int
    T: str

@dataclass
class TransactionObject:
    type: str
    inputs: List[Any]
    outputs: List[Any]

@dataclass
class CoinbaseTransaction:
    type: str
    height: int
    outputs: List[Any]
