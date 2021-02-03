# -*- coding: utf-8 -*-

# pylint: disable=invalid-name,missing-docstring,no-self-use,protected-access

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import re
import unittest
from uuid import uuid4

import responses

from resources.lib import kodiutils
from resources.lib.modules.sources import Source
from resources.lib.modules.sources.external import ExternalSource


class SourcesTest(unittest.TestCase):

    def test_create(self):
        # Clean sources
        filename = os.path.join(kodiutils.addon_profile(), ExternalSource.SOURCES_FILE)
        if os.path.exists(filename):
            os.unlink(filename)

        key = str(uuid4())

        # Create new source
        source = ExternalSource(uuid=key,
                                name='External Source',
                                enabled=False)
        source.save()

        # Check that we can find this source
        sources = ExternalSource.detect_sources()
        self.assertIn(key, [source.uuid for source in sources])
        self.assertEqual(next(source for source in sources if source.uuid == key).enabled, False)

        # Update source
        source.enabled = True
        source.save()

        # Check that we can find this source
        sources = ExternalSource.detect_sources()
        self.assertIn(key, [source.uuid for source in sources])
        self.assertEqual(next(source for source in sources if source.uuid == key).enabled, True)

        # Remove source
        source.delete()

        # Check that we can't find this source anymore
        sources = ExternalSource.detect_sources()
        self.assertNotIn(key, [source.uuid for source in sources])

    def test_fetch_none(self):
        source = ExternalSource(
            uuid=str(uuid4()),
            name='Test Source',
            enabled=True,
            playlist_uri=None,
            playlist_type=ExternalSource.TYPE_NONE,
            epg_uri=None,
            epg_type=ExternalSource.TYPE_NONE,
        )

        channels = source.get_channels()
        self.assertEqual(channels, '')

        epg = source.get_epg()
        self.assertEqual(epg, '')

    def test_fetch_file(self):
        source = ExternalSource(
            uuid=str(uuid4()),
            name='Test Source',
            enabled=True,
            playlist_uri=os.path.realpath('tests/data/external_playlist.m3u'),
            playlist_type=ExternalSource.TYPE_FILE,
            epg_uri=os.path.realpath('tests/data/external_epg.xml'),
            epg_type=ExternalSource.TYPE_FILE,
        )
        expected_channels = Source._extract_m3u(open('tests/data/external_playlist.m3u', 'r').read())
        expected_epg = Source._extract_xmltv(open('tests/data/external_epg.xml', 'r').read())

        # Test channels
        channels = source.get_channels()
        self.assertEqual(channels.replace('\r\n', '\n'), expected_channels)

        # Test channels (gzip)
        source.playlist_uri = os.path.realpath('tests/data/external_playlist.m3u.gz')
        channels = source.get_channels()
        self.assertEqual(channels.replace('\r\n', '\n'), expected_channels)

        # Test EPG
        epg = source.get_epg()
        self.assertEqual(epg.replace('\r\n', '\n'), expected_epg)

    @responses.activate
    def test_fetch_url(self):

        def request_callback(request):
            if request.url.endswith('m3u'):
                data = open('tests/data/external_playlist.m3u', 'rb').read()
                return 200, {}, data

            if request.url.endswith('m3u.gz'):
                data = open('tests/data/external_playlist.m3u', 'rb').read()
                try:  # Python 3
                    from gzip import compress
                    return 200, {}, compress(data)
                except ImportError:  # Python 2
                    from gzip import GzipFile
                    from StringIO import StringIO
                    buf = StringIO()
                    with GzipFile(fileobj=buf, mode='wb') as f:
                        f.write(data)
                    return 200, {}, buf.getvalue()

            if request.url.endswith('m3u.bz2'):
                from bz2 import compress
                data = open('tests/data/external_playlist.m3u', 'rb').read()
                return 200, {}, compress(data)

            if request.url.endswith('xml'):
                data = open('tests/data/external_epg.xml', 'rb').read()
                return 200, {}, data

            return 404, {}, None

        responses.add_callback(responses.GET, re.compile('https://example.com/.*'), callback=request_callback)

        source = ExternalSource(
            uuid=str(uuid4()),
            name='Test Source',
            enabled=True,
            playlist_uri='https://example.com/playlist.m3u',
            playlist_type=ExternalSource.TYPE_URL,
            epg_uri='https://example.com/xmltv.xml',
            epg_type=ExternalSource.TYPE_URL,
        )
        expected_channels = Source._extract_m3u(open('tests/data/external_playlist.m3u', 'r').read())
        expected_epg = Source._extract_xmltv(open('tests/data/external_epg.xml', 'r').read())

        # Test channels
        channels = source.get_channels()
        self.assertEqual(channels.replace('\r\n', '\n'), expected_channels)

        # Test channels (gzip)
        source.playlist_uri = 'https://example.com/playlist.m3u.gz'
        channels = source.get_channels()
        self.assertEqual(channels.replace('\r\n', '\n'), expected_channels)

        # Test channels (bzip2)
        source.playlist_uri = 'https://example.com/playlist.m3u.bz2'
        channels = source.get_channels()
        self.assertEqual(channels.replace('\r\n', '\n'), expected_channels)

        # Test EPG
        epg = source.get_epg()
        self.assertEqual(epg.replace('\r\n', '\n'), expected_epg)


if __name__ == '__main__':
    unittest.main()
