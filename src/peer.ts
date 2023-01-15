import { db } from './database'
import { logger } from './logger'
import { MessageSocket } from './network'
import semver from 'semver'

import {
    Message,
    ErrorMessageType,
    HelloMessage,
    HelloMessageType,
    IHaveObjectMessageType,
    GetObjectMessageType,
    ObjectMessageType,
    GetPeersMessageType,
    PeersMessageType,
    ChainTipMessageType,
    GetChainTipMessageType,
    GetMempoolMessageType,
    MempoolMessageType
} from './message'

import { network } from './network'

import {
    ObjectId,
    objectManager
} from './object'

import { peerManager } from './peermanager'
import { canonicalize } from 'json-canonicalize'
import { Block } from './block'

const VERSION = '0.8.0'
const NAME = 'KOOL Node'

// Number of peers that each peer is allowed to report to us.
const MAX_PEERS_PER_PEER = 30

export class Peer {
    active: boolean = false
    socket: MessageSocket
    handshakeCompleted: boolean = false
    peerAddr: string

    async sendHello() {
        this.sendMessage({
            type: 'hello',
            version: VERSION,
            agent: NAME
        })
    }

    async sendGetPeers() {
        this.sendMessage({
            type: 'getpeers'
        })
    }

    async sendPeers() {
        this.sendMessage({
            type: 'peers',
            peers: [...peerManager.knownPeers]
        })
    }

    async sendIHaveObject(obj: any) {
        this.sendMessage({
            type: 'ihaveobject',
            objectid: objectManager.id(obj)
        })
    }

    async sendObject(obj: any) {
        this.sendMessage({
            type: 'object',
            object: obj
        })
    }

    async sendGetObject(objid: ObjectId) {
        this.sendMessage({
            type: 'getobject',
            objectid: objid
        })
    }

    // Task 4:

    async sendGetChainTip() {
        this.sendMessage({
            type: 'getchaintip'
        })
    }

    async sendChainTip(objid: ObjectId) {
        this.sendMessage({
            type: 'chaintip',
            blockid: objid
        })
    }

    //

    // Task 5:
    
    async sendGetMempool() {
        this.sendMessage({
            type: 'getmempool'
        })
    }

    async sendMempool(txids: Array<ObjectId>) {
        this.sendMessage({
            type: 'mempool',
            txids: txids
        })
    }

    // 

    async sendError(err: string) {
        this.sendMessage({
            type: 'error',
            error: err
        })
    }

    sendMessage(obj: object) {
        const message: string = canonicalize(obj)

        this.debug(`Sending message: ${message}`)
        this.socket.sendMessage(message)
    }

    async fatalError(err: string) {
        await this.sendError(err)
        this.warn(`Peer error: ${err}`)
        this.fail()
    }

    async fail() {
        this.active = false
        this.socket.end()
        peerManager.peerFailed(this.peerAddr)
    }

    async onConnect() {
        this.active = true
        await this.sendHello()
        await this.sendGetPeers()
        await this.sendGetChainTip()
        // Task 5.3
        await this.sendGetMempool()
    }

    async onMessage(message: string) {
        this.debug(`Message arrival: ${message}`)

        let msg: object

        try {
            msg = JSON.parse(message)
            this.debug(`Parsed message into: ${JSON.stringify(msg)}`)
        } catch {
            return await this.fatalError(`Failed to parse incoming message as JSON: ${message}`)
        }

        // Check if the message is in the correct format
        if (!Message.guard(msg)) {
            const validation = Message.validate(msg)
            return await this.fatalError(
                `The received message does not match one of the known message formats: ${message}
         Validation error: ${JSON.stringify(validation)}`
            )
        }

        if (!this.handshakeCompleted) {
            if (HelloMessage.guard(msg)) {
                return this.onMessageHello(msg)
            }
            return await this.fatalError(`Received message ${message} prior to "hello"`)
        }

        Message.match(
            async () => {
                return await this.fatalError(`Received a second "hello" message, even though handshake is completed`)
            },
            this.onMessageGetPeers.bind(this),
            this.onMessagePeers.bind(this),
            this.onMessageIHaveObject.bind(this),
            this.onMessageGetObject.bind(this),
            this.onMessageObject.bind(this),
            // Task 4
            this.onMessageGetChainTip.bind(this),
            this.onMessageChainTip.bind(this),
            //
            this.onMessageGetMempool.bind(this),
            this.onMessageMempool.bind(this),
            this.onMessageError.bind(this)
        )(msg)
    }

    async onMessageHello(msg: HelloMessageType) {
        if (!semver.satisfies(msg.version, `^${VERSION}`)) {
            return await this.fatalError(`You sent an incorrect version (${msg.version}), which is not compatible with this node's version ${VERSION}.`)
        }
        this.info(`Handshake completed. Remote peer running ${msg.agent} at protocol version ${msg.version}`)
        this.handshakeCompleted = true
    }

    async onMessagePeers(msg: PeersMessageType) {
        for (const peer of msg.peers.slice(0, MAX_PEERS_PER_PEER)) {
            this.info(`Remote party reports knowledge of peer ${peer}`)

            peerManager.peerDiscovered(peer)
        }

        if (msg.peers.length > MAX_PEERS_PER_PEER) {
            this.info(`Remote party reported ${msg.peers.length} peers, but we processed only ${MAX_PEERS_PER_PEER} of them.`)
        }
    }

    async onMessageGetPeers(msg: GetPeersMessageType) {
        this.info(`Remote party is requesting peers. Sharing.`)
        await this.sendPeers()
    }

    async onMessageIHaveObject(msg: IHaveObjectMessageType) {
        this.info(`Peer claims knowledge of: ${msg.objectid}`)

        if (!await db.exists(msg.objectid)) {
            this.info(`Object ${msg.objectid} discovered`)
            await this.sendGetObject(msg.objectid)
        }
    }

    async onMessageGetObject(msg: GetObjectMessageType) {
        this.info(`Peer requested object with id: ${msg.objectid}`)

        let obj
        try {
            obj = await objectManager.get(msg.objectid)
        } catch (e) {
            this.warn(`We don't have the requested object with id: ${msg.objectid}`)
            this.sendError(`Unknown object with id ${msg.objectid}`)
            return
        }
        await this.sendObject(obj)
    }

    async onMessageObject(msg: ObjectMessageType) {
        const objectid: ObjectId = objectManager.id(msg.object)
        let known: boolean = false

        this.info(`Received object with id ${objectid}: %o`, msg.object)

        known = await objectManager.exists(objectid)
        if (known) {
            this.debug(`Object with id ${objectid} is already known`)
        } else {
            this.info(`New object with id ${objectid} downloaded: %o`, msg.object)
            // FIXME: Store object even if it is invalid
            await objectManager.put(msg.object)
        }

        try {
            await objectManager.validate(msg.object, this)
        } catch (e: any) {
            this.sendError(`Received invalid object: ${e.message}`)
            return
        }

        if (!known) {
            // gossip
            network.broadcast({
                type: 'ihaveobject',
                objectid
            })
        }
    }

    // Task 4
    async onMessageChainTip(msg: ChainTipMessageType) {
        const known = await objectManager.exists(msg.blockid);
        
        if (known) {
            // if we have it we can try updating, probably redundant
            const block: Block = await objectManager.get(msg.blockid);

            if (block.valid) {
                await network.updateChainTip(block);
            }
        } else {
            // If we don't have the chaintip then get it
            this.info(`Object ${msg.blockid} discovered`)
            await this.sendGetObject(msg.blockid);
        }
    }

    async onMessageGetChainTip(msg: GetChainTipMessageType) {
        const block = await network.getChainTip();

        await this.sendChainTip(block.blockid);
    }
    //

    // Task 5
    async onMessageGetMempool(msg: GetMempoolMessageType) {
        const mempool = await network.getMempool()
        
        await this.sendMempool(mempool);
    }
    

    async onMessageMempool(msg: MempoolMessageType) {
        // Task 5.4
        // Get all the Transactions if we don't have them

        for (const txid in msg.txids) {
            const known = await objectManager.exists(txid);

            if (!known) {
                this.info(`Asking for mempool transaction ${txid}`);
                await this.sendGetObject(txid);
            }
        }
    }
    //

    async onMessageError(msg: ErrorMessageType) {
        this.warn(`Peer reported error: ${msg.error}`)
    }

    log(level: string, message: string, ...args: any[]) {
        logger.log(
            level,
            `[peer ${this.socket.peerAddr}:${this.socket.netSocket.remotePort}] ${message}`,
            ...args
        )
    }

    warn(message: string, ...args: any[]) {
        this.log('warn', message, ...args)
    }

    info(message: string, ...args: any[]) {
        this.log('info', message, ...args)
    }

    debug(message: string, ...args: any[]) {
        this.log('debug', message, ...args)
    }

    constructor(socket: MessageSocket, peerAddr: string) {
        this.socket = socket
        this.peerAddr = peerAddr

        socket.netSocket.on('connect', this.onConnect.bind(this))
        socket.netSocket.on('error', err => {
            this.warn(`Socket error: ${err}`)
            this.fail()
        })
        // Binding the event handler to this
        socket.on('message', this.onMessage.bind(this))
    }
}
