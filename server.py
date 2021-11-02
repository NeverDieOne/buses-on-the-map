import argparse
import json
import logging
from contextlib import suppress
from dataclasses import asdict
from functools import partial

import trio
from trio_websocket import ConnectionClosed, serve_websocket

from bus import Bus, BusValidationError
from window_bounds import WindowBounds, WindowBoundsValidationError

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
            serialized_message = json.loads(message)
            if serialized_message.get('msgType') == 'newBounds':
                WindowBounds.validate(serialized_message)
                window_bounds.update(**serialized_message['data'])
        except ConnectionClosed:
            break
    
        except json.JSONDecodeError:
            await ws.send_message(json.dumps({
                'msgType': 'Errors',
                'errors': 'Requires valid JSON'
            }))
        except WindowBoundsValidationError as e:
            await ws.send_message(json.dumps({
                'msgType': 'Errors',
                'errors': e.args
            }))


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
            serialized_message = json.loads(message)
            Bus.validate(serialized_message)
            BUSES.update({
                serialized_message['busId']: Bus(**serialized_message)
            })
        except ConnectionClosed:
            break
        except json.JSONDecodeError:
            await ws.send_message(json.dumps({
                'msgType': 'Errors',
                'errors': 'Requires valid JSON'
            }))
        except BusValidationError as e:
            await ws.send_message(json.dumps({
                'msgType': 'Errors',
                'errors': e.args
            }))


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
