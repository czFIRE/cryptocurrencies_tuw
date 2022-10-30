from dataclasses import dataclass

@dataclass
class Peer:
    ip: str
    port: int
    agentName: str = ""
    beenConnected: bool = len(agentName) > 0