import functools
import logging

import trio
from trio_websocket import ConnectionClosed, HandshakeError

logger = logging.getLogger(__name__)


def relaunch_on_disconnect(async_function):
    @functools.wraps(async_function)
    async def wrapper(*args):
        while True:
            try:
                return await async_function(*args)
            except (HandshakeError, ConnectionClosed):
                logger.info('Connection error')
                await trio.sleep(5)
    return wrapper
