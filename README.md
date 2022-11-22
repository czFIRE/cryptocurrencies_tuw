# Byzantine Node - Group 01

## Run

Requirements: Docker, Docker Compose

Run with `sh run.sh`

It starts-up a docker container named crypto-node-1 with port 18018 open.

Alternatively run with: `python3 node.py`.

At least Python 3.10 is required.


## Documentation

Logic for first task from Snekel.

At startup the node attempts to connect to the peers in `PRELOADED_PEERS` in
`constants.py`. It will also start listening on the port `PORT`.

Discovered peers are stored in the PeerManager using a SQLLite DB. This data is read on startup.
Localhost and multicast addresses are never added as peers.

Every `SERVICE_LOOP_DELAY` seconds the so-called service loop runs. Currently,
this is where the number of active connections is checked and new connections
are established as needed. If the number of active connections drops below
`LOW_CONNECTION_THRESHOLD`, the node will attempt to establish new connections
to randomly selected peers that it discovered previously.

Upon establishing a connection the node sends a hello and then a getpeers
message. It will wait `HELLO_MSG_TIMEOUT` seconds for a hello message before
closing the connections. After receiving a hello message, the connection will
remain open until an error occurs or until the peer closes it. If an error
message is received the connection is closed as well.

The `BANNED_HOSTS` list contains IP addresses of hosts that should never be
saved as peers. Currently, it includes some public DNS servers and addresses
that seemed to belong to client machines that were inadvertently added by some
peer. We identified these client machines by determining that their IPs showed
up with a large number of different ports in a received peers message and were
not listed in the IP database in TUWEL.

The IP `20.23.212.159` is not a client IP, as it is listed in the IP database
in TUWEL. Nevertheless, we blacklisted it, as some peers distributed this
address with dozens of different ports, making the peer list extremely large. A
related post in TUWEL is here:
https://tuwel.tuwien.ac.at/mod/forum/discuss.php?d=337348

We suspect, that the issue with some IP addresses showing up with a large
number of ports is due to a node adding incoming connections (which use
ephemeral ports on the client side) to the list of peers it then distributes.
We think this is invalid, as it is not possible to connect back to those ports.

