import asyncio
import time
import constants as const
import logging as log

from datetime import timedelta
from global_variables import CONNECTIONS, DB_MANAGER
from connection.connection_handling import bootstrap, listen, resupply_connections


async def init():
    bootstrap_task = asyncio.create_task(bootstrap())
    listen_task = asyncio.create_task(listen())

    await bootstrap_task
    return await listen_task


async def main():
    server = await init()
    start_time = time.time()

    try:
        async with server:
            print(f'- Node is up & running @ {const.HOST}')

            # Service loop
            while True:
                delta_time = timedelta(seconds=time.time() - start_time)
                weeks = delta_time.days//7
                hours = delta_time.seconds//3600
                minutes = (delta_time.seconds//60)%60
                seconds = delta_time.seconds - hours*3600 - minutes*60

                uptime_str = ""
                if weeks:
                    uptime_str += f'{weeks}w '
                if delta_time.days:
                    uptime_str += f'{delta_time.days}d '
                if hours:
                    uptime_str += f'{hours}h '
                if minutes:
                    uptime_str += f'{minutes}m '
                uptime_str += f'{seconds}s'

                log.debug(f"New service loop iteration [Total uptime: {uptime_str}]")
                log.debug(f"Open connections: {list(CONNECTIONS.keys())}")

                # Open more connections if necessary
                delta_peers = const.LOW_CONNECTION_THRESHOLD - len(CONNECTIONS)
                if delta_peers > 0:
                    log.info(f"Too few connections available (currently {len(CONNECTIONS)})")
                    resupply_connections(delta_peers)

                await asyncio.sleep(const.SERVICE_LOOP_DELAY)
    except KeyboardInterrupt:
        await server.wait_closed()
        server.get_loop().run_until_complete(asyncio.gather(*asyncio.all_tasks()))
        DB_MANAGER.close_db_connection()


if __name__ == "__main__":
    log.basicConfig(filename='./persist/kerma_node.log', level=log.DEBUG,
                    format='%(asctime)s | %(levelname)s: %(message)s', force=True)

    # set up logging to console
    console = log.StreamHandler()
    console.setLevel(log.DEBUG)
    # set a format which is simpler for console use
    formatter = log.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    # add the handler to the root logger
    log.getLogger('').addHandler(console)

    logger = log.getLogger(__name__)

    print("- Starting Kerma node...")
    asyncio.run(main())
