import trio
from trio_websocket import open_websocket_url
import json
import logging


async def main():
    try:
        async with open_websocket_url('ws://localhost:8080') as ws:
            await ws.send_message('hello world!')
            message = await ws.get_message()
            print(message)

            await ws.send_message(json.dumps({
                'busId': 123,
                'lng': 35.0,
                'route': "123"
            }))
            message = await ws.get_message()
            print(message)

            await ws.send_message(json.dumps({
                'lat': 35.0,
                'lng': 35.0,
                'route': "123"
            }))
            message = await ws.get_message()
            print(message)
    except OSError as ose:
        logging.error('Connection attempt failed: %s', ose)

trio.run(main)