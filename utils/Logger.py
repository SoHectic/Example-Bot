import colorlog
import logging

class Logger:
    def createLogs(logLocation: str=None):
        handler = colorlog.StreamHandler()
        handler.setFormatter(colorlog.ColoredFormatter('%(log_color)s%(levelname)s - %(name)s : %(message)s - (%(filename)s:%(lineno)d)'))
        logger = colorlog.getLogger('livebot')
        logger.setLevel(colorlog.DEBUG)
        logger.addHandler(handler)
        fh = logging.FileHandler(logLocation, mode="a", encoding="utf-8")
        fh.disable = True
        fh.setFormatter(colorlog.ColoredFormatter('%(levelname)s - %(name)s : %(message)s - (%(filename)s:%(lineno)d)', reset=False))
        logger.addHandler(fh)

        return logger
        
    def debug(msg):
        colorlog.debug(msg)

    def info(msg):
        colorlog.info(msg)

    def warning(msg):
        colorlog.warning(msg)

    def error(msg):
        colorlog.error(msg)

    def critical(msg):
        colorlog.critical(msg)