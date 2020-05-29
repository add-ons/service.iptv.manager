# -*- coding: utf-8 -*-
"""This is a fake addon"""
from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import sys

try:  # Python 3
    from urllib.parse import parse_qsl, urlparse
except ImportError:  # Python 2
    from urlparse import parse_qsl, urlparse

logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger()


class IPTVManager:
    """Interface to IPTV Manager"""

    def __init__(self, port):
        """Initialize IPTV Manager object"""
        self.port = port

    def via_socket(func):  # pylint: disable=no-self-argument
        """Send the output of the wrapped function to socket"""

        def send(self):
            """Decorator to send over a socket"""
            import json
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('127.0.0.1', self.port))
            try:
                sock.send(json.dumps(func()).encode())
            finally:
                sock.close()

        return send

    @via_socket
    def send_channels():  # pylint: disable=no-method-argument
        """Return JSON-STREAMS formatted information to IPTV Manager"""
        streams = [
            dict(
                id='channel1.com',
                name='Channel 1',
                preset=1,
                stream='plugin://plugin.video.example.two/play/1',
                logo='https://example.com/channel1.png',
                vod='plugin://plugin.video.example.two/play/airdate/{date}'
            ),
        ]
        return dict(version=1, streams=streams)

    @via_socket
    def send_epg():  # pylint: disable=no-method-argument
        """Return JSON-EPG formatted information to IPTV Manager"""
        epg = {}
        return dict(version=1, epg=epg)


if __name__ == "__main__":

    if len(sys.argv) <= 1:
        print('ERROR: Missing URL as first parameter')
        exit(1)

    # Parse routing
    url_parts = urlparse(sys.argv[1])
    route = url_parts.path
    query = dict(parse_qsl(url_parts.query))

    if route == '/iptv/channels':
        IPTVManager(int(query['port'])).send_channels()
        exit()

    if route == '/iptv/epg':
        IPTVManager(int(query['port'])).send_epg()
        exit()

    if route.startswith('/play/airdate'):
        _LOGGER.info('Starting playback of program with route %s and query %s', route, query)

        # Touch a file so we can detect that we ended up here correctly
        open('/tmp/playback-started.txt', 'a').close()
        exit()

    _LOGGER.error('Unknown route %s with query %s', route, query)
    exit(1)
