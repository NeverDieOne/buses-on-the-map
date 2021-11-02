import json

import trio
from trio_websocket import serve_websocket, ConnectionClosed


def read_route_file(route_number):
    with open(f'routes/{route_number}.json', 'r') as f:
        return json.load(f)


async def server(request):
    ws = await request.accept()
    route = read_route_file(156)
    coordinates = route['coordinates']

    for coordinate in coordinates:
        lat, lng = coordinate
        try:
            message = {
                "msgType": "Buses",
                "buses": [
                    {"busId": "c790сс", "lat": lat, "lng": lng, "route": "156"},
                ]
            }
            await ws.send_message(json.dumps(message))
            await trio.sleep(1)
        except ConnectionClosed:
            break

async def main():
    await serve_websocket(server, '127.0.0.1', 8000, ssl_context=None)


if __name__ == '__main__':   
    trio.run(main)