from dataclasses import dataclass


@dataclass
class TxObject:
    type: str
    txids: any  # should be array
    nonce: str
    previd: str
    created: int
    T: str


