import pytest
import asyncio
from websockets import connect
import json


@pytest.mark.asyncio
@pytest.mark.skip
async def test_bus():
    async with connect('ws://localhost:8080') as ws:
        message = {
            'busId': "123",
            'lat': 35.0,
            'lng': 35.0,
            'route': "123"
        }
        await ws.send(json.dumps(message))
        print(await ws.recv())


@pytest.mark.asyncio
async def test_client():
    async with connect('ws://localhost:8000') as ws:
        message = {
            "msgType": "newBounds",
            "data": {
                "east_lng": 37.65563964843751,
                "north_lat": 55.77367652953477,
                "south_lat": 55.72628839374007,
                "west_lng": 37.54440307617188,
            },
        }
        await ws.send(json.dumps(message))
        print(await ws.recv())
        print(await ws.recv())
        print(await ws.recv())
        print(await ws.recv())
