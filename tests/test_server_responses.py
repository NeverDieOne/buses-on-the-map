import pytest
import trio
from trio_websocket import open_websocket_url


test_bus_data = [
    ('Hello message','{"msgType": "Errors", "errors": "Requires valid JSON"}'),
    ('{"busId": 123, "lng": 35.0, "route": "123"}', '{"msgType": "Errors", "errors": [["busId must be <class \'str\'>", "lat is required"]]}'),
    ('{"lat": 35.0, "lng": 35.0, "route": "123"}', '{"msgType": "Errors", "errors": [["busId is required"]]}')
]


@pytest.mark.parametrize('test_data,expected_result', test_bus_data)
def test_bus(test_data, expected_result):

    async def async_wrapper():
        async with open_websocket_url('ws://localhost:8080') as ws:
            await ws.send_message(test_data)
            message = await ws.get_message()
            assert message == expected_result

    trio.run(async_wrapper)


test_client_data = [
    ('{"data": {"east_lng": 37.6, "north_lat": 55.77, "south_lat": 55.72, "west_lng": 37.5}}', ''),
    ('Hello message', '{"msgType": "Errors", "errors": "Requires valid JSON"}'),
]


@pytest.mark.parametrize('test_data,expected_result', test_client_data)
def test_client(test_data, expected_result):

    async def async_wrapper():
        async with open_websocket_url('ws://localhost:8000') as ws:
            await ws.send_message(test_data)
            for _ in range(3):
                message = await ws.get_message()
                if 'Errors' in message:
                    assert message == expected_result
    
    trio.run(async_wrapper)
