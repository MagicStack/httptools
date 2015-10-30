from __future__ import print_function
from libc.stdlib cimport malloc, free

from .errors import (HttpParserError,
                     HttpParserCallbackError,
                     HttpParserInvalidStatus,
                     HttpParserInvalidMethod,
                     HttpParserInvalidURL)

cimport cparser

__all__ = ('HttpRequestParser', 'HttpResponseParser')


cdef class HttpParser:

    cdef cparser.http_parser* _cparser
    cdef cparser.http_parser_settings* _csettings

    cdef _proto_on_url, _proto_on_status, _proto_on_body, \
         _proto_on_header, _proto_on_headers_complete, \
         _proto_on_message_complete, _proto_on_chunk_header, \
         _proto_on_chunk_complete

    cdef bytes _current_header_name
    cdef bytes _current_header_value

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
        if self._proto_on_chunk_header is not None:
            self._csettings.on_chunk_header = cb_on_chunk_header

        self._proto_on_chunk_complete = getattr(
            protocol, 'on_chunk_complete', None)
        if self._proto_on_chunk_complete is not None:
            self._csettings.on_chunk_complete = cb_on_chunk_complete

    cdef _on_header_field(self, bytes field):
        if self._current_header_name is not None:
            self._proto_on_header(self._current_header_name,
                                  self._current_header_value)
            self._current_header_value = None

        self._current_header_name = field

    cdef _on_header_value(self, bytes val):
        if self._current_header_value is None:
            self._current_header_value = val
        else:
            # This is unlikely, as mostly HTTP headers are one-line
            self._current_header_value += val

    cdef _on_headers_complete(self):
        if self._current_header_name is not None:
            self._proto_on_header(self._current_header_name,
                                  self._current_header_value)

            self._current_header_value = self._current_header_name = None

        if self._proto_on_headers_complete is not None:
            self._proto_on_headers_complete()

    cdef _on_chunk_header(self):
        if (self._current_header_value is not None or
            self._current_header_name is not None):
            raise HttpParserError('invalid headers state')
        self._proto_on_chunk_header()

    cdef _on_chunk_complete(self):
        if self._current_header_name is not None:
            self._proto_on_header(self._current_header_name,
                                  self._current_header_value)

        self._proto_on_chunk_complete()

    ### Public API ###

    def get_http_version(self):
        cdef cparser.http_parser* parser = self._cparser
        return '{}.{}'.format(parser.http_major, parser.http_minor)

    def should_keep_alive(self):
        return bool(cparser.http_should_keep_alive(self._cparser))

    def feed_data(self, bytes data):
        data_len = len(data)

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
        return (cparser.http_method_str(<cparser.http_method> parser.method)
                .decode('latin-1'))


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
    pyparser = <HttpParser>parser.data
    try:
        pyparser._on_message_begin()
    except:
        return -1
    else:
        return 0


cdef int cb_on_url(cparser.http_parser* parser, const char *at, size_t length):
    pyparser = <HttpParser>parser.data
    try:
        pyparser._proto_on_url(at[:length])
    except:
        return -1
    else:
        return 0


cdef int cb_on_status(cparser.http_parser* parser, const char *at, size_t length):
    pyparser = <HttpParser>parser.data
    try:
        pyparser._proto_on_status(at[:length])
    except:
        return -1
    else:
        return 0


cdef int cb_on_header_field(cparser.http_parser* parser,
                          const char *at, size_t length):
    pyparser = <HttpParser>parser.data
    try:
        pyparser._on_header_field(at[:length])
    except:
        return -1
    else:
        return 0


cdef int cb_on_header_value(cparser.http_parser* parser,
                          const char *at, size_t length):
    pyparser = <HttpParser>parser.data
    try:
        pyparser._on_header_value(at[:length])
    except:
        return -1
    else:
        return 0


cdef int cb_on_headers_complete(cparser.http_parser* parser):
    pyparser = <HttpParser>parser.data
    try:
        pyparser._on_headers_complete()
    except:
        return -1
    else:
        return 0


cdef int cb_on_body(cparser.http_parser* parser, const char *at, size_t length):
    pyparser = <HttpParser>parser.data
    try:
        pyparser._proto_on_body(at[:length])
    except:
        return -1
    else:
        return 0


cdef int cb_on_message_complete(cparser.http_parser* parser):
    pyparser = <HttpParser>parser.data
    try:
        pyparser._proto_on_message_complete()
    except:
        return -1
    else:
        return 0


cdef int cb_on_chunk_header(cparser.http_parser* parser):
    pyparser = <HttpParser>parser.data
    try:
        pyparser._on_chunk_header()
    except:
        return -1
    else:
        return 0


cdef int cb_on_chunk_complete(cparser.http_parser* parser):
    pyparser = <HttpParser>parser.data
    try:
        pyparser._on_chunk_complete()
    except:
        return -1
    else:
        return 0


cdef parser_error_from_errno(cparser.http_errno errno):
    desc = cparser.http_errno_description(errno)

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
        cls = HttpParserInvalidStatus

    elif errno == cparser.HPE_INVALID_METHOD:
        cls = HttpParserInvalidMethod

    elif errno == cparser.HPE_INVALID_URL:
        cls = HttpParserInvalidURL

    else:
        cls = HttpParserError

    return cls(desc.decode('latin-1'))
