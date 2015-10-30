from __future__ import print_function
from libc.stdlib cimport malloc, free

from .errors import (HttpParserError,
                     HttpParserCallbackError,
                     HttpParserInvalidStatusError,
                     HttpParserInvalidMethodError,
                     HttpParserInvalidURLError)

import cython
cimport cparser


__all__ = ('HttpRequestParser', 'HttpResponseParser', 'parse_url')


@cython.internal
cdef class HttpParser:

    cdef:
        cparser.http_parser* _cparser
        cparser.http_parser_settings* _csettings

        bytes _current_header_name
        bytes _current_header_value

        _proto_on_url, _proto_on_status, _proto_on_body, \
        _proto_on_header, _proto_on_headers_complete, \
        _proto_on_message_complete, _proto_on_chunk_header, \
        _proto_on_chunk_complete

    def __cinit__(self, protocol):
        self._cparser = <cparser.http_parser*> \
                                malloc(sizeof(cparser.http_parser))
        if self._cparser is NULL:
            raise MemoryError()

        self._csettings = <cparser.http_parser_settings*> \
                                malloc(sizeof(cparser.http_parser_settings))
        if self._csettings is NULL:
            raise MemoryError()

    def __dealloc__(self):
        if self._cparser is not NULL:
            free(self._cparser)
        if self._csettings is not NULL:
            free(self._csettings)

    cdef _init(self, protocol, cparser.http_parser_type mode):
        cparser.http_parser_init(self._cparser, mode)
        self._cparser.data = <void*>self

        cparser.http_parser_settings_init(self._csettings)

        self._current_header_name = None
        self._current_header_value = None

        self._proto_on_header = getattr(protocol, 'on_header', None)
        if self._proto_on_header is not None:
            self._csettings.on_header_field = cb_on_header_field
            self._csettings.on_header_value = cb_on_header_value
        self._proto_on_headers_complete = getattr(
            protocol, 'on_headers_complete', None)
        self._csettings.on_headers_complete = cb_on_headers_complete

        self._proto_on_body = getattr(protocol, 'on_body', None)
        if self._proto_on_body is not None:
            self._csettings.on_body = cb_on_body

        self._proto_on_message_complete = getattr(
            protocol, 'on_message_complete', None)
        if self._proto_on_message_complete is not None:
            self._csettings.on_message_complete = cb_on_message_complete

        self._proto_on_chunk_header = getattr(
            protocol, 'on_chunk_header', None)
        self._csettings.on_chunk_header = cb_on_chunk_header

        self._proto_on_chunk_complete = getattr(
            protocol, 'on_chunk_complete', None)
        self._csettings.on_chunk_complete = cb_on_chunk_complete

    cdef _maybe_call_on_header(self):
        if self._current_header_name is not None:
            current_header_name = self._current_header_name
            current_header_value = self._current_header_value

            self._current_header_name = self._current_header_value = None

            if self._proto_on_header is not None:
                self._proto_on_header(current_header_name,
                                      current_header_value)

    cdef _on_header_field(self, bytes field):
        self._maybe_call_on_header()
        self._current_header_name = field

    cdef _on_header_value(self, bytes val):
        if self._current_header_value is None:
            self._current_header_value = val
        else:
            # This is unlikely, as mostly HTTP headers are one-line
            self._current_header_value += val

    cdef _on_headers_complete(self):
        self._maybe_call_on_header()

        if self._proto_on_headers_complete is not None:
            self._proto_on_headers_complete()

    cdef _on_chunk_header(self):
        if (self._current_header_value is not None or
            self._current_header_name is not None):
            raise HttpParserError('invalid headers state')

        if self._proto_on_chunk_header is not None:
            self._proto_on_chunk_header()

    cdef _on_chunk_complete(self):
        self._maybe_call_on_header()

        if self._proto_on_chunk_complete is not None:
            self._proto_on_chunk_complete()

    ### Public API ###

    def get_http_version(self):
        cdef cparser.http_parser* parser = self._cparser
        return '{}.{}'.format(parser.http_major, parser.http_minor)

    def should_keep_alive(self):
        return bool(cparser.http_should_keep_alive(self._cparser))

    def feed_data(self, bytes data):
        cdef:
            size_t data_len = len(data)
            int nb

        nb = cparser.http_parser_execute(
            self._cparser,
            self._csettings,
            data,
            data_len)

        # TODO: Handle parser->upgrade

        if self._cparser.http_errno != cparser.HPE_OK:
            raise parser_error_from_errno(
                <cparser.http_errno> self._cparser.http_errno)
        if nb != data_len:
            raise HttpParserError('not all of the data was parsed')


cdef class HttpRequestParser(HttpParser):

    def __init__(self, protocol):
        self._init(protocol, cparser.HTTP_REQUEST)

        self._proto_on_url = getattr(protocol, 'on_url', None)
        if self._proto_on_url is not None:
            self._csettings.on_url = cb_on_url

    def get_method(self):
        cdef cparser.http_parser* parser = self._cparser
        return cparser.http_method_str(<cparser.http_method> parser.method)


cdef class HttpResponseParser(HttpParser):

    def __init__(self, protocol):
        self._init(protocol, cparser.HTTP_RESPONSE)

        self._proto_on_status = getattr(protocol, 'on_status', None)
        if self._proto_on_status is not None:
            self._csettings.on_status = cb_on_status

    def get_status_code(self):
        cdef cparser.http_parser* parser = self._cparser
        return parser.status_code


cdef int cb_on_message_begin(cparser.http_parser* parser):
    cdef HttpParser pyparser = <HttpParser>parser.data
    try:
        pyparser._on_message_begin()
    except:
        return -1
    else:
        return 0


cdef int cb_on_url(cparser.http_parser* parser, const char *at, size_t length):
    cdef HttpParser pyparser = <HttpParser>parser.data
    try:
        pyparser._proto_on_url(at[:length])
    except:
        return -1
    else:
        return 0


cdef int cb_on_status(cparser.http_parser* parser, const char *at, size_t length):
    cdef HttpParser pyparser = <HttpParser>parser.data
    try:
        pyparser._proto_on_status(at[:length])
    except:
        return -1
    else:
        return 0


cdef int cb_on_header_field(cparser.http_parser* parser,
                          const char *at, size_t length):
    cdef HttpParser pyparser = <HttpParser>parser.data
    try:
        pyparser._on_header_field(at[:length])
    except:
        return -1
    else:
        return 0


cdef int cb_on_header_value(cparser.http_parser* parser,
                          const char *at, size_t length):
    cdef HttpParser pyparser = <HttpParser>parser.data
    try:
        pyparser._on_header_value(at[:length])
    except:
        return -1
    else:
        return 0


cdef int cb_on_headers_complete(cparser.http_parser* parser):
    cdef HttpParser pyparser = <HttpParser>parser.data
    try:
        pyparser._on_headers_complete()
    except:
        return -1
    else:
        return 0


cdef int cb_on_body(cparser.http_parser* parser, const char *at, size_t length):
    cdef HttpParser pyparser = <HttpParser>parser.data
    try:
        pyparser._proto_on_body(at[:length])
    except:
        return -1
    else:
        return 0


cdef int cb_on_message_complete(cparser.http_parser* parser):
    cdef HttpParser pyparser = <HttpParser>parser.data
    try:
        pyparser._proto_on_message_complete()
    except:
        return -1
    else:
        return 0


cdef int cb_on_chunk_header(cparser.http_parser* parser):
    cdef HttpParser pyparser = <HttpParser>parser.data
    try:
        pyparser._on_chunk_header()
    except:
        return -1
    else:
        return 0


cdef int cb_on_chunk_complete(cparser.http_parser* parser):
    cdef HttpParser pyparser = <HttpParser>parser.data
    try:
        pyparser._on_chunk_complete()
    except:
        return -1
    else:
        return 0


cdef parser_error_from_errno(cparser.http_errno errno):
    cdef bytes desc = cparser.http_errno_description(errno)

    if errno in (cparser.HPE_CB_message_begin,
                 cparser.HPE_CB_url,
                 cparser.HPE_CB_header_field,
                 cparser.HPE_CB_header_value,
                 cparser.HPE_CB_headers_complete,
                 cparser.HPE_CB_body,
                 cparser.HPE_CB_message_complete,
                 cparser.HPE_CB_status,
                 cparser.HPE_CB_chunk_header,
                 cparser.HPE_CB_chunk_complete):
        cls = HttpParserCallbackError

    elif errno == cparser.HPE_INVALID_STATUS:
        cls = HttpParserInvalidStatusError

    elif errno == cparser.HPE_INVALID_METHOD:
        cls = HttpParserInvalidMethodError

    elif errno == cparser.HPE_INVALID_URL:
        cls = HttpParserInvalidURLError

    else:
        cls = HttpParserError

    return cls(desc.decode('latin-1'))


cdef class URL:
    cdef bytes _schema
    cdef bytes _host
    cdef object _port
    cdef bytes _path
    cdef bytes _query
    cdef bytes _fragment
    cdef bytes _userinfo

    def __cinit__(self, bytes schema, bytes host, object port, bytes path,
                  bytes query, bytes fragment, bytes userinfo):

        self._schema = schema
        self._host = host
        self._port = port
        self._path = path
        self._query = query
        self._fragment = fragment
        self._userinfo = userinfo

    property schema:
        def __get__(self):
            return self._schema

    property host:
        def __get__(self):
            return self._host

    property port:
        def __get__(self):
            return self._port

    property path:
        def __get__(self):
            return self._path

    property query:
        def __get__(self):
            return self._query

    property fragment:
        def __get__(self):
            return self._fragment

    property userinfo:
        def __get__(self):
            return self._userinfo

    def __repr__(self):
        return ('<URL schema: {!r}, host: {!r}, port: {!r}, path: {!r}, '
                'query: {!r}, fragment: {!r}, userinfo: {!r}>'
                .format(self.schema, self.host, self.port, self.path,
                    self.query, self.fragment, self.userinfo))


def parse_url(bytes url):
    cdef:
        size_t url_len = len(url)
        cparser.http_parser_url* parsed
        int res
        bytes schema = None
        bytes host = None
        object port = None
        bytes path = None
        bytes query = None
        bytes fragment = None
        bytes userinfo = None
        object result = None
        int off
        int ln

    parsed = <cparser.http_parser_url*> malloc(sizeof(cparser.http_parser_url))
    cparser.http_parser_url_init(parsed)

    try:
        res = cparser.http_parser_parse_url(url, url_len, 0, parsed)
        if res == 0:
            if parsed.field_set & (1 << cparser.UF_SCHEMA):
                off = parsed.field_data[<int>cparser.UF_SCHEMA].off
                ln = parsed.field_data[<int>cparser.UF_SCHEMA].len
                schema = url[off:off+ln]

            if parsed.field_set & (1 << cparser.UF_HOST):
                off = parsed.field_data[<int>cparser.UF_HOST].off
                ln = parsed.field_data[<int>cparser.UF_HOST].len
                host = url[off:off+ln]

            if parsed.field_set & (1 << cparser.UF_PORT):
                port = parsed.port

            if parsed.field_set & (1 << cparser.UF_PATH):
                off = parsed.field_data[<int>cparser.UF_PATH].off
                ln = parsed.field_data[<int>cparser.UF_PATH].len
                path = url[off:off+ln]

            if parsed.field_set & (1 << cparser.UF_QUERY):
                off = parsed.field_data[<int>cparser.UF_QUERY].off
                ln = parsed.field_data[<int>cparser.UF_QUERY].len
                query = url[off:off+ln]

            if parsed.field_set & (1 << cparser.UF_FRAGMENT):
                off = parsed.field_data[<int>cparser.UF_FRAGMENT].off
                ln = parsed.field_data[<int>cparser.UF_FRAGMENT].len
                fragment = url[off:off+ln]

            if parsed.field_set & (1 << cparser.UF_USERINFO):
                off = parsed.field_data[<int>cparser.UF_USERINFO].off
                ln = parsed.field_data[<int>cparser.UF_USERINFO].len
                userinfo = url[off:off+ln]

            return URL(schema, host, port, path, query, fragment, userinfo)
        else:
            raise HttpParserInvalidURLError("invalid url {!r}".format(url))
    finally:
        free(parsed)
