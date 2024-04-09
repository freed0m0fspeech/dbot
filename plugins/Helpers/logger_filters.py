import logging
from discord import ConnectionClosed


class GatewayEventFilter(logging.Filter):
    def __init__(self) -> None:
        super().__init__('discord.gateway')

    def filter(self, record: logging.LogRecord) -> bool:
        if record.exc_info is not None and isinstance(record.exc_info[1], ConnectionClosed):
            return False
        return True
