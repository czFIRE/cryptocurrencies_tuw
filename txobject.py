from dataclasses import dataclass
from typing import Any, List

@dataclass
class TxObject:
    type: str
    txids: List[Any] # should be array
    nonce: str
    previd: str
    created: int
    T: str


