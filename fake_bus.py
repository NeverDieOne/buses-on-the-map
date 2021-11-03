import argparse
import json
import logging
import os
import time
from contextlib import suppress
from itertools import cycle, islice
from random import choice, randint

import trio
from trio_websocket import open_websocket_url

from async_decorators import relaunch_on_disconnect

logger = logging.getLogger(__name__)


def get_args():
    parser = argparse.ArgumentParser(description='Fake bus')
    parser.add_argument(
        '-s', '--server',
        help='Адрес сервера',
        default='ws://localhost:8080'
    )
    parser.add_argument(
        '-rn', '--routes_number',
        help='Количество маршрутов',
        type=int
    )
    parser.add_argument(
        '-bpr', '--buses_per_route',
        help='Количество автобусов на маршруте',
        default=1,
        type=int
    )
    parser.add_argument(
        '-wsn', '--websocket_number',
        help='Количество открытых вебсокетов',
        default=1,
        type=int
    )
    parser.add_argument(
        '-emid', '--emulator_id',
        help='Префикс к busId на случай запуска нескольких экземпляров',
        default=time.time()
    )
    parser.add_argument(
        '-rt', '--refresh_timeout',
        help='Задержка в обновлении координат сервера',
        default=1,
        type=int
    )
    parser.add_argument(
        '-v', '--verbose',
        help='Показывать логи',
        action='store_true'
    )
    return parser.parse_args()


def generate_bus_id(route_id, bus_index, emulator_id):
    return f'{route_id}-{bus_index}-{emulator_id}'


def load_routes(directory_path='routes'):
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, 'r', encoding='utf8') as file:
                yield json.load(file)


async def run_bus(
    send_channel, route_id, route, bus_index, emulator_id, refresh_timeout
):
    start_position = randint(1, 10)
    cycle_route = route[start_position:] + list(reversed(route[start_position:]))
    for coordinate in cycle(cycle_route):
        lat, lng = coordinate
        await send_channel.send({
            'busId': generate_bus_id(route_id, bus_index, emulator_id),
            'lat': lat,
            'lng': lng,
            'route': route_id
        })
        await trio.sleep(refresh_timeout)


@relaunch_on_disconnect
async def send_updates(server_address, reveive_channel):
    async with open_websocket_url(server_address) as ws:
        async for message in reveive_channel:
            await ws.send_message(json.dumps(message, ensure_ascii=False))


async def main():
    args = get_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    logger.info(f'Open {args.websocket_number} channels')
    channels = [trio.open_memory_channel(0) for _ in range(args.websocket_number)]

    with suppress(KeyboardInterrupt):
        async with trio.open_nursery() as nursery:
            for _, receive_channel in channels:
                nursery.start_soon(
                    send_updates,
                    args.server,
                    receive_channel
                )

            logger.info(f'Read {args.routes_number} routes files')
            logger.info(f'Start {args.buses_per_route} buses per route')
            for route in islice(load_routes(), args.routes_number):
                for bus_index in range(args.buses_per_route):
                    send_channel, _ = choice(channels)
                    nursery.start_soon(
                        run_bus,
                        send_channel,
                        route['name'],
                        route['coordinates'],
                        bus_index,
                        args.emulator_id,
                        args.refresh_timeout
                    )


if __name__ == '__main__':
    trio.run(main)
