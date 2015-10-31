import httptools

import unittest
from unittest import mock


RESPONSE1_HEAD = b'''HTTP/1.1 200 OK
Date: Mon, 23 May 2005 22:38:34 GMT
Server: Apache/1.3.3.7
        (Unix) (Red-Hat/Linux)
Last-Modified: Wed, 08 Jan 2003 23:11:55 GMT
ETag: "3f80f-1b6-3e1cb03b"
Content-Type: text/html;
  charset=UTF-8
Content-Length: 130
Accept-Ranges: bytes
Connection: close

'''

RESPONSE1_BODY = b'''
<html>
<head>
  <title>An Example Page</title>
</head>
<body>
  Hello World, this is a very simple HTML document.
</body>
</html>'''


CHUNKED_REQUEST1_1 = b'''POST /test.php?a=b+c HTTP/1.2
User-Agent: Fooo
Host: bar
Transfer-Encoding: chunked

5\r\nhello\r\n6\r\n world\r\n'''

CHUNKED_REQUEST1_2 = b'''0\r\nVary: *\r\nUser-Agent: spam\r\n\r\n'''


class TestResponseParser(unittest.TestCase):

    def test_parser_response_1(self):
        m = mock.Mock()

        headers = {}
        m.on_header.side_effect = headers.__setitem__

        p = httptools.HttpResponseParser(m)
        p.feed_data(RESPONSE1_HEAD)

        self.assertEqual(p.get_http_version(), '1.1')
        self.assertEqual(p.get_status_code(), 200)

        m.on_status.assert_called_once_with(b'OK')

        m.on_headers_complete.assert_called_once_with()
        self.assertEqual(m.on_header.call_count, 8)
        self.assertEqual(len(headers), 8)
        self.assertEqual(headers.get(b'Connection'), b'close')
        self.assertEqual(headers.get(b'Content-Type'),
                         b'text/html;  charset=UTF-8')

        self.assertFalse(m.on_body.called)
        p.feed_data(bytearray(RESPONSE1_BODY))
        m.on_body.assert_called_once_with(RESPONSE1_BODY)

        m.on_message_complete.assert_called_once_with()

        self.assertFalse(m.on_url.called)
        self.assertFalse(m.on_chunk_header.called)
        self.assertFalse(m.on_chunk_complete.called)

        with self.assertRaisesRegex(
            httptools.HttpParserError,
            'data received after completed connection'):

            p.feed_data(b'12123123')

    def test_parser_response_2(self):
        with self.assertRaisesRegex(TypeError, 'expected bytes'):
            httptools.HttpResponseParser(None).feed_data('')

    def test_parser_response_3(self):
        callbacks = {'on_header', 'on_headers_complete', 'on_body',
                     'on_message_complete'}

        for cbname in callbacks:
            with self.subTest('{} callback fails correctly'.format(cbname)):
                with self.assertRaisesRegex(httptools.HttpParserCallbackError,
                                            'callback failed'):

                    m = mock.Mock()
                    getattr(m, cbname).side_effect = Exception()

                    p = httptools.HttpResponseParser(m)
                    p.feed_data(RESPONSE1_HEAD + RESPONSE1_BODY)

    def test_parser_response_4(self):
        p = httptools.HttpResponseParser(None)
        with self.assertRaises(httptools.HttpParserInvalidStatusError):
            p.feed_data(b'HTTP/1.1 1299 FOOSPAM\r\n')

    def test_parser_response_5(self):
        m = mock.Mock()
        m.on_status = None
        m.on_header = None
        m.on_body = None
        m.on_headers_complete = None
        m.on_chunk_header = None
        m.on_chunk_complete = None

        p = httptools.HttpResponseParser(m)
        p.feed_data(RESPONSE1_HEAD)
        p.feed_data(RESPONSE1_BODY)

        m.on_message_complete.assert_called_once_with()


class TestRequestParser(unittest.TestCase):

    def test_parser_request_chunked_1(self):
        m = mock.Mock()
        p = httptools.HttpRequestParser(m)

        p.feed_data(CHUNKED_REQUEST1_1)

        self.assertEqual(p.get_method(), b'POST')

        m.on_url.assert_called_once_with(b'/test.php?a=b+c')
        self.assertEqual(p.get_http_version(), '1.2')

        m.on_header.assert_called_with(b'Transfer-Encoding', b'chunked')
        m.on_chunk_header.assert_called_with()
        m.on_chunk_complete.assert_called_with()

        self.assertFalse(m.on_message_complete.called)

        m.reset_mock()
        p.feed_data(CHUNKED_REQUEST1_2)

        m.on_chunk_header.assert_called_with()
        m.on_chunk_complete.assert_called_with()
        m.on_header.assert_called_with(b'User-Agent', b'spam')
        self.assertEqual(m.on_header.call_count, 2)

        m.on_message_complete.assert_called_once_with()

    def test_parser_request_chunked_2(self):
        m = mock.Mock()

        headers = {}
        m.on_header.side_effect = headers.__setitem__

        m.on_url = None
        m.on_body = None
        m.on_headers_complete = None
        m.on_chunk_header = None
        m.on_chunk_complete = None

        p = httptools.HttpRequestParser(m)
        p.feed_data(CHUNKED_REQUEST1_1)
        p.feed_data(CHUNKED_REQUEST1_2)

        self.assertEqual(
            headers,
            {b'User-Agent': b'spam',
             b'Transfer-Encoding': b'chunked',
             b'Host': b'bar',
             b'Vary': b'*'})

    def test_parser_request_2(self):
        p = httptools.HttpRequestParser(None)
        with self.assertRaises(httptools.HttpParserInvalidMethodError):
            p.feed_data(b'SPAM /test.php?a=b+c HTTP/1.2')

    def test_parser_request_3(self):
        p = httptools.HttpRequestParser(None)
        with self.assertRaises(httptools.HttpParserInvalidURLError):
            p.feed_data(b'POST  HTTP/1.2')


class TestUrlParser(unittest.TestCase):

    def parse(self, url:bytes):
        parsed = httptools.parse_url(url)
        return (parsed.schema, parsed.host, parsed.port, parsed.path,
                parsed.query, parsed.fragment, parsed.userinfo)

    def test_parser_url_1(self):
        self.assertEqual(
            self.parse(b'dsf://aaa/b/c?aa#123'),
            (b'dsf', b'aaa', None, b'/b/c', b'aa', b'123', None))

        self.assertEqual(
            self.parse(b'dsf://i:n@aaa:88/b/c?aa#123'),
            (b'dsf', b'aaa', 88, b'/b/c', b'aa', b'123', b'i:n'))

        self.assertEqual(
            self.parse(b'////'),
            (None, None, None, b'////', None, None, None))

        self.assertEqual(
            self.parse(b'////1/1?a=b&c[]=d&c[]=z'),
            (None, None, None, b'////1/1', b'a=b&c[]=d&c[]=z', None, None))

        self.assertEqual(
            self.parse(b'/////?#123'),
            (None, None, None, b'/////', None, b'123', None))

        self.assertEqual(
            self.parse(b'/a/b/c?b=1&'),
            (None, None, None, b'/a/b/c', b'b=1&', None, None))

    def test_parser_url_2(self):
        self.assertEqual(
            self.parse(b''),
            (None, None, None, None, None, None, None))

    def test_parser_url_3(self):
        with self.assertRaises(httptools.HttpParserInvalidURLError):
            self.parse(b' ')

    def test_parser_url_4(self):
        with self.assertRaises(httptools.HttpParserInvalidURLError):
            self.parse(b':///1')

    def test_parser_url_5(self):
        self.assertEqual(
            self.parse(b'http://[1:2::3:4]:67/'),
            (b'http', b'1:2::3:4', 67, b'/', None, None, None))

    def test_parser_url_6(self):
        self.assertEqual(
            self.parse(bytearray(b'/')),
            (None, None, None, b'/', None, None, None))
