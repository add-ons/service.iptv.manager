# -*- coding: utf-8 -*-
"""This is a fake addon"""
from __future__ import absolute_import, division, print_function, unicode_literals

import datetime
import sys

import dateutil.parser
import dateutil.tz
import xbmc
import xbmcplugin

try:  # Python 3
    from urllib.parse import parse_qsl, urlparse
except ImportError:  # Python 2
    from urlparse import parse_qsl, urlparse


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
                stream='plugin://plugin.video.example/play/1',
                logo='https://example.com/channel1.png',
                kodiprops={
                    'inputstream': 'inputstream.ffmpegdirect',
                    'inputstream.ffmpegdirect.is_realtime_stream': 'true',
                    'mimetype': 'video/mp2t',
                },
            ),
            dict(
                id='channel2.com',
                name='Channel 2',
                preset=2,
                stream='plugin://plugin.video.example/play/2',
                logo='https://example.com/channel2.png',
            ),
            dict(
                id='radio1.com',
                name='Radio 1',
                preset=901,
                stream='plugin://plugin.video.example/play/901',
                logo='https://example.com/radio1.png',
                group='VRT',
                radio=True,
            ),
            dict(
                id='één.be',
                name='één',
                preset=101,
                stream='plugin://plugin.video.example/play/één',
                logo='https://example.com/één.png',
                group=['Belgium', 'VRT'],
            ),
        ]
        return dict(version=1, streams=streams)

    @via_socket
    def send_epg():  # pylint: disable=no-method-argument
        """Return JSON-EPG formatted information to IPTV Manager"""
        now = datetime.datetime.now(tz=dateutil.tz.gettz('CET'))
        now_notz = datetime.datetime.now()

        epg = {
            'channel1.com': [
                dict(
                    start=now.isoformat(),
                    stop=(now + datetime.timedelta(seconds=1800)).isoformat(),
                    title='This is a show with an & ampersand.',
                    description='This is the description of the show € 4 + 4 > 6',
                    subtitle='Pilot episode',
                    genre='Quiz',
                    episode='S01E01',
                    image='https://example.com/image.png',
                    date='1987-06-15',
                    stream='plugin://plugin.video.example/play/something',
                ),
                dict(
                    start=(now + datetime.timedelta(seconds=1800)).isoformat(),
                    stop=(now + datetime.timedelta(seconds=3600)).isoformat(),
                    title='This is a show 2 named "Show 2"',
                    description='This is the description of the show 2',
                    image=None,
                    stream='plugin://plugin.video.example/play/something',
                )
            ],
            'channel2.com': [
                dict(
                    start=now_notz.isoformat(),
                    stop=(now_notz + datetime.timedelta(seconds=1800)).isoformat(),
                    title='This is a show 3 (no timezone info)',
                    description='This is the description of the show 3',
                    image=None,
                    stream='plugin://plugin.video.example/play/something',
                ),
                dict(
                    start=(now_notz + datetime.timedelta(seconds=1800)).isoformat(),
                    stop=(now_notz + datetime.timedelta(seconds=3600)).isoformat(),
                    title='This is a show 4 (no timezone info)',
                    description='This is the description of the show 4',
                    image=None,
                    stream='plugin://plugin.video.example/play/something',
                )
            ],
            'één.be': [
                dict(
                    start=now.isoformat(),
                    stop=(now + datetime.timedelta(seconds=1800)).isoformat(),
                    title='This is a show on één.',
                    description='This is the description of the show on één',
                    subtitle='Pilot episode',
                    episode='S01E01',
                    image='https://example.com/image.png',
                    date='1987-06-15',
                    stream='plugin://plugin.video.example/play/something',
                    credits=[
                        {
                            "type": "director",
                            "name": "David Benioff"
                        },
                        {
                            "type": "director",
                            "name": "D.B. Weiss"
                        },
                        {
                            "type": "actor",
                            "name": "Kit Harington",
                            "role": "Jon Snow"
                        },
                        {
                            "type": "actor",
                            "name": "Emilia Clarke",
                            "role": "Daenerys Targaryen"
                        },
                        {
                            "type": "writer",
                            "name": "George R.R. Martin"
                        },
                    ]
                )
            ],
        }
        return dict(version=1, epg=epg)


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
    print('Invoked plugin.video.example with route %s and query %s' % (route, query))

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
