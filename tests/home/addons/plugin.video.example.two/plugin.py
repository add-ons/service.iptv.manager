# -*- coding: utf-8 -*-
"""This is a fake addon"""
from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import os
import sys
import tempfile

try:  # Python 3
    from urllib.parse import parse_qsl, urlsplit
except ImportError:  # Python 2
    from urlparse import parse_qsl, urlsplit

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
                logo='https://example.com/channel1.png'
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

    # Remove the first argument
    sys.argv.pop(0)

    # Parse routing
    path = urlsplit(sys.argv[0]).path or '/'
    if len(sys.argv) > 2:
        params = dict(parse_qsl(sys.argv[2].lstrip('?')))
    else:
        params = {}

    if path == '/iptv/channels':
        IPTVManager(int(params['port'])).send_channels()
        exit()

    if path == '/iptv/epg':
        IPTVManager(int(params['port'])).send_epg()
        exit()

    if path.startswith('/play'):
        _LOGGER.info('Starting playback of program with route %s and query %s', route, query)

        # Touch a file so we can detect that we ended up here correctly
        playback_started = os.path.join(tempfile.gettempdir(), 'playback-started.txt')
        open(playback_started, 'a').close()
        exit()

    _LOGGER.error('Unknown route %s with query %s', path, params)
    exit(1)
