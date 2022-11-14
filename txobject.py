from dataclasses import dataclass, asdict
from typing import Any, List, Dict
import json

from hashlib import sha256 

from jcs import canonicalize

@dataclass
class BlockObject:
    type: str
    txids: List[Any] # should be array
    nonce: str
    previd: str
    created: int
    T: str
    miner: str
    note: str

    def __repr__(self) -> str:
        return json.dumps(asdict(self)) 

    def __hash__(self) -> int:
        return int(self.sha256(), base=16)

    def asdict(self) -> Dict[str, Any]:
        return asdict(self)

    def sha256(self):
        return sha256(canonicalize(asdict(self))).hexdigest()  # type: ignore

@dataclass
class TransactionObject:
    type: str
    inputs: List[Any]
    outputs: List[Any]

    def __repr__(self) -> str:
        return json.dumps(asdict(self)) 

    def __hash__(self) -> int:
        return int(self.sha256(), base=16)

    def asdict(self) -> Dict[str, Any]:
        return asdict(self)


    def sha256(self):
        return sha256(canonicalize(asdict(self))).hexdigest() # type: ignore

@dataclass
class CoinbaseTransaction:
    type: str
    height: int
    outputs: List[Any]

    def __repr__(self) -> str:
        return json.dumps(asdict(self)) 

    def __hash__(self) -> int:
        return int(self.sha256(), base=16)

    def asdict(self) -> Dict[str, Any]:
        return asdict(self)

    def sha256(self):
        return sha256(canonicalize(asdict(self))).hexdigest()  # type: ignore
