import json
from functools import partial
import logging
from dataclasses import dataclass, asdict
from contextlib import suppress
import argparse

import trio
from trio_websocket import serve_websocket, ConnectionClosed

from bus import Bus
from window_bounds import WindowBounds


BUSES = {}
logger = logging.getLogger()


def get_args():
    parser = argparse.ArgumentParser(description='Bus server')
    parser.add_argument(
        '-s', '--server',
        help='Адрес сервера',
        default='127.0.0.1'
    )
    parser.add_argument(
        '-bp', '--bus_port',
        help='Под для имитатора автобусов',
        default=8080,
        type=int
    )
    parser.add_argument(
        '-brp', '--browser_port',
        help='Порт для браузера',
        default=8000,
        type=int
    )
    parser.add_argument(
        '-v', '--verbose',
        help='Настройка логирования',
        action='store_true'
    )
    return parser.parse_args()


async def listen_browser(ws, window_bounds):
    while True:
        try:
            message = await ws.get_message()
            window_bounds.update(**json.loads(message)['data'])
        except ConnectionClosed:
            break


async def send_buses(ws, window_bounds):
    while True:
        try:
            buses = [
                asdict(bus) for bus in list(BUSES.values())
                if window_bounds.is_inside(bus.lat, bus.lng)
            ]

            await ws.send_message(json.dumps({
                "msgType": "Buses",
                "buses": buses
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
            BUSES.update({bus_info['busId']: Bus(**bus_info)})
        except ConnectionClosed:
            break


async def talk_to_browser(request):
    ws = await request.accept()

    window_bounds = WindowBounds()
    async with trio.open_nursery() as nursery:
        nursery.start_soon(listen_browser, ws, window_bounds)
        nursery.start_soon(send_buses, ws, window_bounds)


async def main():
    args = get_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    with suppress(KeyboardInterrupt):
        async with trio.open_nursery() as nursery:
            nursery.start_soon(
                partial(
                    serve_websocket,
                    listen_server,
                    args.server,
                    args.bus_port,
                    ssl_context=None
                )
            )
            nursery.start_soon(
                partial(
                    serve_websocket,
                    talk_to_browser,
                    args.server,
                    args.browser_port,
                    ssl_context=None
                    )
                )


if __name__ == '__main__':   
    trio.run(main)
