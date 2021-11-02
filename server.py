import json
from functools import partial
import logging

import trio
from trio_websocket import serve_websocket, ConnectionClosed


BUSES = {}
logger = logging.getLogger()


async def listen_browser(ws):
    while True:
        try:
            message = await ws.get_message()
            logger.info(message)
        except ConnectionClosed:
            break


async def send_browser(ws):
    while True:
        try:
            await ws.send_message(json.dumps({
                "msgType": "Buses",
                "buses": list(BUSES.values())
            }))
            await trio.sleep(1)
        except ConnectionClosed:
            break


async def listen_server(request):
    ws = await request.accept()

    while True:
        try:
            message = await ws.get_message()
            bus_info = json.loads(message)
            BUSES.update({bus_info['busId']: bus_info})
        except ConnectionClosed:
            break


async def talk_to_browser(request):
    ws = await request.accept()

    async with trio.open_nursery() as nursery:
        nursery.start_soon(send_browser, ws)
        nursery.start_soon(listen_browser, ws)


async def main():
    logging.basicConfig(level=logging.INFO)

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