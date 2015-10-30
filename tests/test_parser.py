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
        p.feed_data(RESPONSE1_BODY)
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
        with self.assertRaises(httptools.HttpParserInvalidStatus):
            p.feed_data(b'HTTP/1.1 1299 FOOSPAM\r\n')



class TestRequestParser(unittest.TestCase):

    def test_parser_request_chunked_1(self):
        m = mock.Mock()
        p = httptools.HttpRequestParser(m)

        p.feed_data(CHUNKED_REQUEST1_1)

        self.assertEqual(p.get_method(), 'POST')

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
        p = httptools.HttpRequestParser(None)
        with self.assertRaises(httptools.HttpParserInvalidMethod):
            p.feed_data(b'SPAM /test.php?a=b+c HTTP/1.2')

    def test_parser_request_chunked_3(self):
        p = httptools.HttpRequestParser(None)
        with self.assertRaises(httptools.HttpParserInvalidURL):
            p.feed_data(b'POST  HTTP/1.2')
