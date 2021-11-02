import json
import os
from itertools import cycle, islice
from random import randint, choice

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


async def run_bus(send_channel, route_id, route, bus_index):
    start_position = randint(1, 30)
    for coordinate in cycle(islice(route, start_position, len(route))):
        lat, lng = coordinate
        await send_channel.send({
            'busId': generate_bus_id(route_id, bus_index),
            'lat': lat,
            'lng': lng,
            'route': route_id
        })
        await trio.sleep(1)


async def send_updates(server_address, reveive_channel):
    async with open_websocket_url(server_address) as ws:
        async for message in reveive_channel:
            await ws.send_message(json.dumps(message, ensure_ascii=False))


async def main():
    channels = [trio.open_memory_channel(0) for _ in range(50)]

    try:
        async with trio.open_nursery() as nursery:
            for _, receive_channel in channels:
                nursery.start_soon(
                    send_updates,
                    'ws://localhost:8080',
                    receive_channel
                )

            for route in load_routes():
                for bus_index in range(35):
                    send_channel, _ = choice(channels)
                    nursery.start_soon(
                        run_bus,
                        send_channel,
                        route['name'],
                        route['coordinates'],
                        bus_index
                    )
    except Exception as e:
        print(e)


if __name__ == '__main__':
    trio.run(main)
