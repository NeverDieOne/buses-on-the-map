import json

import trio
from trio_websocket import open_websocket_url


def read_route_file(route_number):
    with open(f'routes/{route_number}.json', 'r') as f:
        return json.load(f)


async def send_route_messages(ws, route_number):
    route = read_route_file(route_number)
    for coordinate in route['coordinates']:
        lat, lng = coordinate
        message = {
            'busId': 'someId',
            'lat': lat,
            'lng': lng,
            'route': route_number
        }

        await ws.send_message(json.dumps(message))
        await trio.sleep(1)


async def main():
    try:
        async with open_websocket_url('ws://localhost:8080') as ws:
            await send_route_messages(ws, 156)
    except Exception as e:
        print(e)


if __name__ == '__main__':
    trio.run(main)
