import * as ed from '@noble/ed25519'
import sha256 from 'fast-sha256'

export type PublicKey = string
export type Signature = string

function hex2uint8(hex: string) {
  return Uint8Array.from(Buffer.from(hex, 'hex'))
}

export async function ed25519_verify(sig: Signature, message: string, pubkey: PublicKey) {
  const pubkeyBuffer = hex2uint8(pubkey)
  const sigBuffer = hex2uint8(sig)
  const messageBuffer = Uint8Array.from(Buffer.from(message, 'utf-8'))
  
  return await ed.verify(sigBuffer, messageBuffer, pubkeyBuffer)
}

export function hash(str: string) {
  const encoder = new TextEncoder()
  const hash = sha256(encoder.encode(str))
  const hashHex = Buffer.from(hash).toString('hex')

  return hashHex
}
