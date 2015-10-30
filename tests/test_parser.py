import httptools

import unittest
from unittest import mock


RESPONSE1_HEAD = br'''HTTP/1.1 200 OK
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
RESPONSE1_BODY = br'''
<html>
<head>
  <title>An Example Page</title>
</head>
<body>
  Hello World, this is a very simple HTML document.
</body>
</html>'''


class TestParser(unittest.TestCase):
    def test_parser_1(self):
        headers = {}

        m = mock.Mock()
        m.on_header.side_effect = lambda k, v: headers.__setitem__(k, v)

        p = httptools.HttpResponseParser(m)
        p.feed_data(RESPONSE1_HEAD)
        p.feed_data(RESPONSE1_BODY)

        self.assertEqual(p.get_http_version(), '1.1')
        self.assertEqual(p.get_status_code(), 200)

        m.on_status.assert_called_once_with(b'OK')

        m.on_headers_complete.assert_called_once_with()
        self.assertEqual(m.on_header.call_count, 8)
        self.assertEqual(len(headers), 8)
        self.assertEqual(headers.get(b'Connection'), b'close')
        self.assertEqual(headers.get(b'Content-Type'),
                         b'text/html;  charset=UTF-8')


        m.on_body.assert_called_once_with(RESPONSE1_BODY)
        m.on_message_complete.assert_called_once_with()

        self.assertFalse(m.on_url.called)
        self.assertFalse(m.on_chunk_header.called)
        self.assertFalse(m.on_chunk_complete.called)
