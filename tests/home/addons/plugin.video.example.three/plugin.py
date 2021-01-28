# -*- coding: utf-8 -*-
"""This is a fake addon"""
from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import sys

import xbmc
import xbmcplugin

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
        channels = """#EXTM3U
#EXTINF:-1 tvg-name="Test 1" tvg-id="raw1.com" tvg-logo="https://example.com/raw1.png" tvg-chno="1" group-title="Test Addon" catchup="vod",RAW 1
plugin://plugin.video.test/play/raw"""
        return channels

    @via_socket
    def send_epg():  # pylint: disable=no-method-argument
        """Return JSON-EPG formatted information to IPTV Manager"""
        epg = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE tv SYSTEM "xmltv.dtd">
<tv source-info-url="http://www.schedulesdirect.org/" source-info-name="Schedules Direct" generator-info-name="XMLTV/$Id: tv_grab_na_dd.in,v 1.70 2008/03/03 15:21:41 rmeden Exp $" generator-info-url="http://www.xmltv.org/">
<channel id="raw1.com"></channel>
<programme start="20210123114255 +0100" stop="20210123121255 +0100" channel="raw1.com" catchup-id="plugin://plugin.video.test/play/raw/1">
 <title>RAW 1</title>
 <desc>RAW 1 description</desc>
</programme>
</tv>"""
        return epg


if __name__ == "__main__":

    if len(sys.argv) <= 1:
        print('ERROR: Missing URL as first parameter')
        exit(1)

    # Parse routing
    url_parts = urlparse(sys.argv[0])
    route = url_parts.path
    if len(sys.argv) > 2:
        query = dict(parse_qsl(sys.argv[2].lstrip('?')))
    else:
        query = {}
    print('Invoked plugin.video.example.three with route %s and query %s' % (route, query))

    if route == '/iptv/channels':
        IPTVManager(int(query['port'])).send_channels()
        exit()

    elif route == '/iptv/epg':
        IPTVManager(int(query['port'])).send_epg()
        exit()

    elif route.startswith('/play'):
        listitem = xbmc.ListItem(label='Something', path='something.mp4')
        xbmcplugin.setResolvedUrl(-1, True, listitem)
        exit()

    # Unknown route
    print('Unknown route %s' % route)
    exit(1)
