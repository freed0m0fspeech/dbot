import logging
from discord import ConnectionClosed


class GatewayEventFilter(logging.Filter):
    def __init__(self) -> None:
        super().__init__('discord.gateway')

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if record.exc_info is not None and isinstance(record.exc_info[1], ConnectionClosed):
                return False
        except Exception:
            pass

        return True

class YouTubeLogFilter(logging.Filter):
    def debug(self, msg):
        logging.debug(msg)

    def warning(self, msg):
        logging.info(msg)

    def error(self, msg):
        logging.error(msg)

class LogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        print('---------------------------------------')
        print('LogFilter')

        try:
            print(record.exc_info)
        except Exception as e:
            print('No record.exc_info')

        try:
            print(record.exc_info[1])
        except Exception as e:
            print('No record.exc_info[1]')

        print('---------------------------------------')

        return True

