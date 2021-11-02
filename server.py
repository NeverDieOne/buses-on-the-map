import json
from functools import partial

import trio
from trio_websocket import serve_websocket, ConnectionClosed


buses = {}


async def listen_server(request):
    ws = await request.accept()

    while True:
        try:
            message = await ws.get_message()
            bus_info = json.loads(message)
            buses.update({bus_info['busId']: bus_info})
        except ConnectionClosed:
            break


async def talk_to_browser(request):
    ws = await request.accept()

    while True:
        try:
            await ws.send_message(json.dumps({
                "msgType": "Buses",
                "buses": list(buses.values())
            }))
            await trio.sleep(1)
        except ConnectionClosed:
            break


async def main():
    listen_fake_bus_partial = partial(
        serve_websocket,
        listen_server,
        '127.0.0.1',
        8080,
        ssl_context=None
    )
    talk_to_browser_partial = partial(
        serve_websocket,
        talk_to_browser,
        '127.0.0.1',
        8000,
        ssl_context=None
    )
    async with trio.open_nursery() as nursery:
        nursery.start_soon(listen_fake_bus_partial)
        nursery.start_soon(talk_to_browser_partial)


if __name__ == '__main__':   
    trio.run(main)