import pytest
from trio_websocket import open_websocket_url


@pytest.mark.asyncio
async def test_bus():
    async with open_websocket_url('ws://localhost:8080') as ws:
        message = {
            'busId': generate_bus_id(route_id, bus_index, args.emulator_id),
            'lat': lat,
            'lng': lng,
            'route': route_id
        }
        await ws.send_message(json.dumps(message))


@pytest.mark.asyncio
async def test_client():
    1 == 1
