__all__ = ('HttpParserError',
           'HttpParserCallbackError',
           'HttpParserInvalidStatus',
           'HttpParserInvalidMethod',
           'HttpParserInvalidURL')


class HttpParserError(Exception):
    pass


class HttpParserCallbackError(HttpParserError):
    pass


class HttpParserInvalidStatus(HttpParserError):
    pass


class HttpParserInvalidMethod(HttpParserError):
    pass


class HttpParserInvalidURL(HttpParserError):
    pass
