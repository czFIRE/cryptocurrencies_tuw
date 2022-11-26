import ipaddress

import logging as log

class Peer:
    def __init__(self, host: str, port: int):
        self.port = port

        try:
            ip = ipaddress.ip_address(host)
            if ip.version == 4:
                self.host = str(ip)
            else:
                # Literal IPv6 Address for specifying ports
                self.host = f'[{ip.compressed}]'

        except ValueError as e:
            log.error(f"Invalid IP!, {e}")
            # Not an IP! It's probably a hostname instead....
            self.host = host

    def to_tuple(self) -> tuple[str, int]:
        return self.host, self.port

    def __str__(self) -> str:
        return f'{self.host}:{self.port}'

    def __eq__(self, o: object) -> bool:
        return isinstance(o, Peer) \
               and self.host == o.host \
               and self.port == o.port

    def __hash__(self) -> int:
        return (self.port, self.host).__hash__()

    def __repr__(self) -> str:
        return self.__str__()
