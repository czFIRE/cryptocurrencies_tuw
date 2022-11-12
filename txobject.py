from dataclasses import dataclass
from typing import Any

@dataclass
class TxObject:
    type: str
    txids: list[Any] # should be array
    nonce: str
    previd: str
    created: int
    T: str


