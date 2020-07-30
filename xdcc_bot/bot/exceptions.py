import logging
logger = logging.getLogger("mainlogger")

class NoReply(Exception):
    def __init__(self):
        super().__init__()
        logger.debug("Exception occured ~| (NoReply)")

class ConnectionFailure(Exception):
    def __init__(self):
        super().__init__()
        logger.debug("Exception occured ~| (ConnectionFailure)")

class DownloadIncomplete(Exception):
    def __init__(self):
        super().__init__()
        logger.debug("Exception occured ~| (DownloadIncomplete)")

class DownloadComplete(Exception):
    def __init__(self):
        super().__init__()
        logger.debug("Exception occured ~| (DownloadComplete)")

class AlreadyDownloaded(Exception):
    def __init__(self):
        super().__init__()
        logger.debug("Exception occured ~| (AlreadyDownloaded)")

class XDCCSocketError(Exception):
    def __init__(self):
        super().__init__()
        logger.debug("Exception occured ~| (XDCCSocketError)")

class NoSuchNick(Exception):
    def __init__(self):
        super().__init__()
        logger.debug("Exception occured ~| (NoSuchNick)")

class AckerError(Exception):
    def __init__(self):
        super().__init__()
        logger.debug("Exception occured ~| (AckerError)")

class TooManyRetries(Exception):
    def __init__(self):
        super().__init__()
        logger.debug("Exception occured ~| (TooManyRetries)")

class ReverseXDCC(Exception):
    def __init__(self):
        super().__init__()
        logger.debug("Exception occured ~| (ReverseXDCC)")
