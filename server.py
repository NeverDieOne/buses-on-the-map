import json
from functools import partial
import logging
from dataclasses import dataclass, asdict

import trio
from trio_websocket import serve_websocket, ConnectionClosed


BUSES = {}
logger = logging.getLogger()


@dataclass
class Bus:
    busId: str
    lat: float
    lng: float
    route: str


@dataclass
class WindowBounds:
    south_lat: float = 0.0
    north_lat: float = 0.0
    west_lng: float = 0.0
    east_lng: float = 0.0

    def is_inside(self, lat, lng):
        return all([
            self.south_lat < lat < self.north_lat,
            self.west_lng < lng < self.east_lng
        ])

    def update(self, south_lat, north_lat, west_lng, east_lng):
        self.south_lat = south_lat
        self.north_lat = north_lat
        self.west_lng = west_lng
        self.east_lng = east_lng


async def listen_browser(ws, window_bounds):
    while True:
        try:
            message = await ws.get_message()
            window_bounds.update(**json.loads(message)['data'])
        except ConnectionClosed:
            logger.info('Browser connection lost')


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
            logger.info('Browser connection lost')


async def listen_server(request):
    ws = await request.accept()

    while True:
        try:
            message = await ws.get_message()
            bus_info = json.loads(message)
            BUSES.update({bus_info['busId']: Bus(**bus_info)})
        except ConnectionClosed:
            logger.info('Browser connection lost')


async def talk_to_browser(request):
    ws = await request.accept()

    window_bounds = WindowBounds()

    async with trio.open_nursery() as nursery:
        nursery.start_soon(listen_browser, ws, window_bounds)
        nursery.start_soon(send_buses, ws, window_bounds)


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