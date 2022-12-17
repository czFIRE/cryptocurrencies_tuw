import { logger } from './logger'
import { network } from './network'

const BIND_PORT = 18018
const BIND_IP = '0.0.0.0'

logger.info(`Kool Node - Group 28`)
logger.info(`Petr Kadlec, Florian Tesarek, Lea Haug Sandberg`)

async function main() {
  network.init(BIND_PORT, BIND_IP)
}

main()