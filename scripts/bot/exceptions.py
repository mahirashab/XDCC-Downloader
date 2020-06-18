

class NoReply(Exception):
    pass

class ConnectionFailure(Exception):
    pass

class DownloadIncomplete(Exception):
    pass

class DownloadComplete(Exception):
    pass

class AlreadyDownloaded(Exception):
    pass

class XDCCSocketError(Exception):
    pass

class NoSuchNick(Exception):
    pass