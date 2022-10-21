


class Connection:

    def __init__(self, address) -> None:
        self.address = address
        # maybe also add the socket connection and such and maybe also the thread?

    def __del__(self) -> None:
        # close the connection when out of scope or destroyed
        
        pass
    
    def send_hello(self) -> bool:
        return False

    def send_peers(self) -> bool:
        return False

    def receive_hello(self) -> bool:
        return False

    def recieve_peers(self) -> bool:
        return False   

    

    def run(self) -> None:
        pass
    