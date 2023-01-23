import { logger } from './logger'
import { EventEmitter } from 'events'
import { Peer } from './peer'
import { peerManager } from './peermanager'
import * as net from 'net'
// Task 4:
import { Block } from './block'

import { Mutex } from 'async-mutex'
import { ObjectId, objectManager } from './object'
import { Transaction } from './transaction'
import { UTXOSet } from './utxo'

class Network {
    peers: Peer[] = []

    // Task 4
    chaintip!: Block
    chaintipMutex: Mutex = new Mutex();
    // 

    // Task 5
    mempool: Array<ObjectId> = [] // set of transactions 
    mempoolUTXO: UTXOSet = new UTXOSet(new Set<string>())
    mempoolMutex: Mutex = new Mutex();
    // TODO

    async init(bindPort: number, bindIP: string) {
        await peerManager.load()

        this.chaintip = await Block.makeGenesis();

        const server = net.createServer(socket => {
            logger.info(`New connection from peer ${socket.remoteAddress}`)
            const peer = new Peer(
                new MessageSocket(socket, `${socket.remoteAddress}:${socket.remotePort}`),
                `${socket.remoteAddress}:${socket.remotePort}`
            )
            this.peers.push(peer)
            peer.onConnect()
        })

        logger.info(`Listening for connections on port ${bindPort} and IP ${bindIP}`)
        server.listen(bindPort, bindIP)

        for (const peerAddr of peerManager.knownPeers) {
            logger.info(`Attempting connection to known peer ${peerAddr}`)
            try {
                const peer = new Peer(
                    MessageSocket.createClient(peerAddr),
                    peerAddr
                )
                this.peers.push(peer)
            } catch (e: any) {
                logger.warn(`Failed to create connection to peer ${peerAddr}: ${e.message}`)
            }
        }
    }

    broadcast(obj: object) {
        logger.info(`Broadcasting object to all peers: %o`, obj)

        for (const peer of this.peers) {
            if (peer.active) {
                peer.sendMessage(obj) // intentionally delayed
            }
        }
    }

    async getChainTip(): Promise<Block> {
        // this line is making sure we have this value
        let retval = this.chaintip;
        await this.chaintipMutex.runExclusive(() => {
            retval = this.chaintip
        });
        // return after we know there wasn't anyone writing into the chaintip
        return retval;
    }

    async updateChainTip(block: Block): Promise<boolean> {
        if (block.height === undefined) {
            //remove this ugly hack. This second check is just here because the height of the genesis block didn't seem to be set to 0 correctly - and nobody knows why :D
            if (block.previd === null) {
                block.height = 0;
                logger.debug(`Set block height to 0`);
            } else {
                logger.error(`This block doesn't have height: ${block.blockid}`);
                return false;
            }
        }

        if (block.height < this.chaintip.height!) {
            return false;
        }

        let retval = false;

        await this.chaintipMutex.runExclusive(() => {
            if (block.height! >= this.chaintip.height!) {
                this.chaintip = block;
                retval = true;
                logger.info(`Chaintip updated to block ${block.blockid} with height ${block.height}`);
            }
        });

        if (retval) {
            await this.mempoolMutex.runExclusive(() => {
                if (block.stateAfter !== undefined) {
                    this.mempoolUTXO = block.stateAfter?.copy()
                }
            })

            // Task 5.6
            // removing those that are in the block
            // TODO TODO don't we want here to get all the TXIDS from the UTXO set this block has?
            await network.removeFromMempool(block.txids)
            // 

            // TODO check if now any of the transactions from the mempool aren't invalid with the UTXO
            let new_mempool: Array<ObjectId> = [];
            
            await this.mempoolMutex.runExclusive(async () => {
                for (let txid in this.mempool) {
                    const tx: Transaction = await objectManager.get(txid);
    
                    try {
                        this.mempoolUTXO.applyMultiple([tx])
    
                        new_mempool.push(txid)
                    } catch (error) {
                        // TODO I guess this is fine?
                    }
                }

                this.mempool = new_mempool;
            })


        }

        return retval;
    }

    // Task 5:
    async getMempool(): Promise<Array<ObjectId>> {
        let retval = this.mempool;

        await this.mempoolMutex.runExclusive(() => {
            retval = this.mempool;
        })

        return retval;
    }

    async addToMempool(tx: Transaction): Promise<null|any> {
        let retval = null;

        await this.mempoolMutex.runExclusive(() => {
            if (!this.mempool.includes(tx.txid)) {
                try {
                    this.mempoolUTXO.applyMultiple([tx]) // can throw error

                    this.mempool.push(tx.txid);
                } catch (error: any) {
                    retval = error.message;
                }
            }
        })

        return retval;
    }

    async removeFromMempool(txids: Array<ObjectId>): Promise<Boolean> {
        let retval = false;

        await this.mempoolMutex.runExclusive(() => {
            const mempoolLength = this.mempool.length
            this.mempool = this.mempool.filter(txid => !txids.includes(txid))
            retval = this.mempool.length < mempoolLength
        })

        return retval;
    }

    async reorganiseMempool(): Promise<Boolean> {
        // Task 5.7 TODO
        return false;
    }

    //
}

export class MessageSocket extends EventEmitter {
    buffer: string = '' // defragmentation buffer
    netSocket: net.Socket
    peerAddr: string

    static createClient(peerAddr: string) {
        const [host, portStr] = peerAddr.split(':')
        const port = +portStr
        if (port < 0 || port > 65535) {
            throw new Error('Invalid port')
        }

        const netSocket = new net.Socket()
        const socket = new MessageSocket(netSocket, peerAddr)
        netSocket.connect(port, host)

        return socket
    }

    constructor(netSocket: net.Socket, peerAddr: string) {
        super()

        this.peerAddr = peerAddr
        this.netSocket = netSocket
        this.netSocket.on('data', (data: string) => {
            this.buffer += data
            const messages = this.buffer.split('\n')

            if (messages.length > 1) {
                for (const message of messages.slice(0, -1)) {
                    this.emit('message', message)
                }
                this.buffer = messages[messages.length - 1]
            }
        })
    }

    sendMessage(message: string) {
        this.netSocket.write(`${message}\n`)
    }

    end() {
        this.netSocket.end()
    }
}

export const network = new Network()
