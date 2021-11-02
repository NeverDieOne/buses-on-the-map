import json
import os
from itertools import cycle, islice
from random import randint

import trio
from trio_websocket import open_websocket_url


def generate_bus_id(route_id, bus_index):
    return f'{route_id}-{bus_index}'


def load_routes(directory_path='routes'):
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, 'r', encoding='utf8') as file:
                yield json.load(file)


async def run_bus(url, route_id, route, bus_index):
    async with open_websocket_url(url) as ws:
        start_position = randint(1, 30)
        for coordinate in cycle(islice(route, start_position, len(route))):
            lat, lng = coordinate
            message = {
                'busId': generate_bus_id(route_id, bus_index),
                'lat': lat,
                'lng': lng,
                'route': route_id
            }

            await ws.send_message(json.dumps(message, ensure_ascii=False))
            await trio.sleep(1)


async def main():
    try:
        async with trio.open_nursery() as nursery:
            for route in load_routes():
                for bus_index in range(2):
                    nursery.start_soon(
                        run_bus,
                        'ws://localhost:8080',
                        route['name'],
                        route['coordinates'],
                        bus_index
                    )
    except Exception as e:
        print(e)


if __name__ == '__main__':
    trio.run(main)
