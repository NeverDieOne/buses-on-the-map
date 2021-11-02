import json
import os

import trio
from trio_websocket import open_websocket_url


def load_routes(directory_path='routes'):
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, 'r', encoding='utf8') as file:
                yield json.load(file)


async def run_bus(url, bus_id, route):
    async with open_websocket_url(url) as ws:
        for coordinate in route:
            lat, lng = coordinate
            message = {
                'busId': bus_id,
                'lat': lat,
                'lng': lng,
                'route': bus_id
            }

            await ws.send_message(json.dumps(message, ensure_ascii=False))
            await trio.sleep(1)


async def main():
    try:
        async with trio.open_nursery() as nursery:
            for route in load_routes():
                nursery.start_soon(
                    run_bus,
                    'ws://localhost:8080',
                    route['name'],
                    route['coordinates']
                )
    except Exception as e:
        print(e)


if __name__ == '__main__':
    trio.run(main)
