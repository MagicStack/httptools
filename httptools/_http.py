from .parser import HttpRequestParser, HttpResponseParser, parse_url
from typing import Union

__all__ = ('HttpRequest', 'HttpResponse')


class HttpParserProtocol:
    def __init__(self, message):
        self._message = message
        self._header_buffer = []
        self._body_buffer = []

    def on_header(self, name: Union[bytes, None], value: Union[bytes, None]):
        self._header_buffer.append((name, value))

    def on_headers_complete(self):
        _headers = {}
        _name = None
        _buffer = None
        _buffer_full = False
        for name, value in self._header_buffer:
            if name is not None:
                _name = None
                if _buffer_full or _buffer is None:
                    _buffer = [name]
                    _buffer_full = False
                else:
                    _buffer.append(name)
            if value is not None:
                if _name is None:
                    _name = b''.join(_buffer)
                    _buffer = None
                if _name not in _headers:
                    _headers[_name] = [value]
                else:
                    _headers[_name].append(value)
                _buffer_full = True
        self._message.headers.update({name: b''.join(value) for name, value in _headers.items()})

    def on_body(self, body: bytes):
        self._body_buffer.append(body)

    def on_message_complete(self):
        self._message.body = b''.join(self._body_buffer)


class HttpRequestParserProtocol(HttpParserProtocol):
    def __init__(self, request):
        HttpParserProtocol.__init__(self, request)

    def on_url(self, url: bytes):
        self._message.url = parse_url(url)


class HttpHeaders(dict):
    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    def __getitem__(self, key):
        return dict.__getitem__(self, key.upper())

    def __setitem__(self, key, value):
        dict.__setitem__(self, key.upper(), value)

    def update(self, *args, **kwargs):
        for key, value in dict(*args, **kwargs).items():
            self[key] = value


class _HttpMessage:
    def __init__(self, parser, protocol: HttpParserProtocol):
        self.headers = HttpHeaders()
        self.body = b''
        self._parser = parser(protocol(self))

    def get_http_version(self) -> bytes:
        return self._parser.get_http_version()

    def feed_data(self, data: bytes):
        self._parser.feed_data(data)

    def should_keep_alive(self) -> bool:
        return self._parser.should_keep_alive()


class HttpRequest(_HttpMessage):
    def __init__(self):
        _HttpMessage.__init__(self, HttpRequestParser, HttpRequestParserProtocol)
        self.url = None

    def get_http_method(self) -> bytes:
        return self._parser.get_method()


class HttpResponse(_HttpMessage):
    def __init__(self):
        _HttpMessage.__init__(self, HttpResponseParser, HttpParserProtocol)

    def get_status_code(self) -> int:
        return self._parser.get_status_code()
