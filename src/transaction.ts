import {
  ed25519_verify,
  PublicKey,
  Signature
} from './crypto'
import { canonicalize } from 'json-canonicalize'
import { logger } from './logger'
import {
  TransactionInputObjectType,
  TransactionObjectType,
  TransactionOutputObjectType,
  OutpointObjectType,
  SpendingTransactionObject
} from './message'
import {
  ObjectId,
  objectManager
} from './object'

export class Output {
  pubkey: PublicKey
  value: number

  static fromNetworkObject(outputMsg: TransactionOutputObjectType): Output {
    return new Output(outputMsg.pubkey, outputMsg.value)
  }

  constructor(pubkey: PublicKey, value: number) {
    this.pubkey = pubkey
    this.value = value
  }
  
  toNetworkObject(): TransactionOutputObjectType {
    return {
      pubkey: this.pubkey,
      value: this.value
    }
  }
}

export class Outpoint {
  txid: ObjectId
  index: number

  constructor(txid: ObjectId, index: number) {
    this.txid = txid
    this.index = index
  }

  static fromNetworkObject(outpoint: OutpointObjectType): Outpoint {
    return new Outpoint(outpoint.txid, outpoint.index)
  }

  async resolve(): Promise<Output> {
    const refTxMsg = await objectManager.get(this.txid)
    const refTx = Transaction.fromNetworkObject(refTxMsg)

    if (this.index >= refTx.outputs.length) {
      throw new Error(`Invalid index reference ${this.index} for transaction ${this.txid}. The transaction only has ${refTx.outputs.length} outputs.`)
    }
    return refTx.outputs[this.index]
  }

  toNetworkObject(): OutpointObjectType {
    return {
      txid: this.txid,
      index: this.index
    }
  }

  toString() {
    return `<outpoint: (${this.txid}, ${this.index})>`
  }
}

export class Input {
  outpoint: Outpoint
  sig: Signature | null

  constructor(outpoint: Outpoint, sig: Signature | null = null) {
    this.outpoint = outpoint
    this.sig = sig
  }

  static fromNetworkObject(inputMsg: TransactionInputObjectType): Input {
    return new Input(
      Outpoint.fromNetworkObject(inputMsg.outpoint),
      inputMsg.sig
    )
  }
  
  toNetworkObject(): TransactionInputObjectType {
    return {
      outpoint: this.outpoint.toNetworkObject(),
      sig: this.sig
    }
  }

  toUnsigned(): Input {
    return new Input(this.outpoint)
  }
}

export class Transaction {
  txid: ObjectId
  inputs: Input[] = []
  outputs: Output[] = []
  height: number | null = null
  fees: number | undefined

  constructor(txid: ObjectId, inputs: Input[], outputs: Output[], height: number | null = null) {
    this.txid = txid
    this.inputs = inputs
    this.outputs = outputs
    this.height = height
  }

  static inputsFromNetworkObject(inputMsgs: TransactionInputObjectType[]) {
    return inputMsgs.map(Input.fromNetworkObject)
  }

  static outputsFromNetworkObject(outputMsgs: TransactionOutputObjectType[]) {
    return outputMsgs.map(Output.fromNetworkObject)
  }

  static fromNetworkObject(txObj: TransactionObjectType): Transaction {
    let inputs: Input[] = []
    let height: number | null = null

    if (SpendingTransactionObject.guard(txObj)) {
      inputs = Transaction.inputsFromNetworkObject(txObj.inputs)
    } else {
      height = txObj.height
    }
    const outputs = Transaction.outputsFromNetworkObject(txObj.outputs)

    return new Transaction(objectManager.id(txObj), inputs, outputs, height)
  }

  static async byId(txid: ObjectId): Promise<Transaction> {
    return this.fromNetworkObject(await objectManager.get(txid))
  }

  isCoinbase() {
    return this.inputs.length === 0
  }

  async validate() {
    logger.debug(`Validating transaction ${this.txid}`)
    const unsignedTxStr = canonicalize(this.toNetworkObject(false))

    if (this.isCoinbase()) {
      if (this.outputs.length > 1) {
        throw new Error(`Invalid coinbase transaction ${this.txid}. Coinbase must have only a single output.`)
      }
      this.fees = 0
      return
    }

    const inputValues = await Promise.all(
      this.inputs.map(async (input, i) => {
        const prevOutput = await input.outpoint.resolve()

        if (input.sig === null) {
          throw new Error(`No signature available for input ${i} of transaction ${this.txid}`)
        }
        if (!await ed25519_verify(input.sig, unsignedTxStr, prevOutput.pubkey)) {
          throw new Error(`Signature validation failed for input ${i} of transaction ${this.txid}`)
        }

        return prevOutput.value
      })
    )

    let sumInputs = 0
    let sumOutputs = 0

    logger.debug(`Checking the law of conservation for transaction ${this.txid}`)
    for (const inputValue of inputValues) {
      sumInputs += inputValue
    }

    logger.debug(`Sum of inputs is ${sumInputs}`)
    for (const output of this.outputs) {
      sumOutputs += output.value
    }

    logger.debug(`Sum of outputs is ${sumOutputs}`)
    if (sumInputs < sumOutputs) {
      throw new Error(`Transaction ${this.txid} does not respect the Law of Conservation. Inputs summed to ${sumInputs}, while outputs summed to ${sumOutputs}.`)
    }
    
    this.fees = sumInputs - sumOutputs
    logger.debug(`Transaction ${this.txid} pays fees ${this.fees}`)
    logger.debug(`Transaction ${this.txid} is valid`)
  }

  inputsUnsigned() {
    return this.inputs.map(
      input => input.toUnsigned().toNetworkObject()
    )
  }

  toNetworkObject(signed: boolean = true): TransactionObjectType {
    const outputObjs = this.outputs.map(output => output.toNetworkObject())

    if (this.height !== null) {
      // coinbase
      return {
        type: 'transaction',
        outputs: outputObjs,
        height: this.height
      }
    }

    if (signed) {
      return {
        type: 'transaction',
        inputs: this.inputs.map(input => input.toNetworkObject()),
        outputs: outputObjs
      }
    }

    return {
      type: 'transaction',
      inputs: this.inputsUnsigned(),
      outputs: outputObjs
    }
  }

  toString() {
    return `<Transaction ${this.txid}>`
  }
}
