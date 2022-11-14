from dataclasses import dataclass
from typing import Any, List

from dataclasses import dataclass, asdict
import json

@dataclass
class BlockObject:
    type: str
    txids: List[Any] # should be array
    nonce: str
    previd: str
    created: int
    T: str

    def __repr__(self) -> str:
        return json.dumps(asdict(self)) 

@dataclass
class TransactionObject:
    type: str
    inputs: List[Any]
    outputs: List[Any]

    def __repr__(self) -> str:
        return json.dumps(asdict(self)) 

@dataclass
class CoinbaseTransaction:
    type: str
    height: int
    outputs: List[Any]

    def __repr__(self) -> str:
        return json.dumps(asdict(self)) 
