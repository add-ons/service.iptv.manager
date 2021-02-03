# -*- coding: utf-8 -*-
"""Tests for Integration"""

# pylint: disable=invalid-name,missing-docstring,no-self-use

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import re
import time
import unittest
import sys
import time
import unittest
from uuid import uuid4

import lxml.etree
import xbmc
from mock import patch
from xbmcgui import ListItem

from resources.lib import kodiutils
from resources.lib.modules.contextmenu import ContextMenu
from resources.lib.modules.sources import Sources
from resources.lib.modules.sources.external import ExternalSource


class IntegrationTest(unittest.TestCase):
    """Integration Tests"""

    def test_refresh(self):
        """Test the refreshing of data."""
        m3u_path = 'tests/home/userdata/addon_data/service.iptv.manager/playlist.m3u8'
        epg_path = 'tests/home/userdata/addon_data/service.iptv.manager/epg.xml'
        sources_path = 'tests/home/userdata/addon_data/service.iptv.manager/sources.json'

        # Remove existing files
        for path in [m3u_path, epg_path, sources_path]:
            if os.path.exists(path):
                os.unlink(path)

        # Add an external source
        source = ExternalSource(uuid=str(uuid4()),
                                name='External Source',
                                enabled=True,
                                playlist_type=ExternalSource.TYPE_FILE,
                                playlist_uri=os.path.realpath('tests/data/external_playlist.m3u'),
                                epg_type=ExternalSource.TYPE_FILE,
                                epg_uri=os.path.realpath('tests/data/external_epg.xml'))
        source.save()

        # Do the refresh
        with patch('xbmcgui.DialogProgress.iscanceled', return_value=False):
            Sources.refresh(True)

        # Check that the files now exist
        for path in [m3u_path, epg_path]:
            self.assertTrue(os.path.exists(path), '%s does not exist' % path)

        # Validate playlist
        with open(m3u_path, 'rb') as fdesc:
            data = kodiutils.to_unicode(fdesc.read())
            self.assertTrue('#EXTM3U' in data)
            self.assertTrue('channel1.com' in data)
            self.assertTrue('channel2.com' in data)
            self.assertTrue('radio1.com' in data)
            self.assertTrue('één.be' in data)
            self.assertTrue('raw1.com' in data)
            self.assertTrue('custom1.com' in data)
            self.assertTrue('custom2.com' in data)
            self.assertTrue('#KODIPROP:inputstream=inputstream.ffmpegdirect' in data)

            # Check groups
            # self.assertRegex doesn't exists in Python 2.7, and self.assertRegexpMatches throws warnings in Python 3
            self.assertTrue(re.search(r'#EXTINF:-1 .*?tvg-id="channel1.com".*?group-title="Example IPTV Addon"', data))
            self.assertTrue(re.search(r'#EXTINF:-1 .*?tvg-id="één.be".*?group-title=".*?VRT.*?"', data))
            self.assertTrue(re.search(r'#EXTINF:-1 .*?tvg-id="één.be".*?group-title=".*?Belgium.*?"', data))
            self.assertTrue(re.search(r'#EXTINF:-1 .*?tvg-id="één.be".*?group-title=".*?Example IPTV Addon.*?"', data))
            self.assertTrue(re.search(r'#EXTINF:-1 .*?tvg-id="radio1.com".*?group-title=".*?VRT.*?"', data))
            self.assertTrue(re.search(r'#EXTINF:-1 .*?tvg-id="radio1.com".*?group-title=".*?Example IPTV Addon.*?"', data))

        # Validate EPG
        xml = lxml.etree.parse(epg_path)
        validator = lxml.etree.DTD('tests/xmltv.dtd')
        self.assertTrue(validator.validate(xml), msg=validator.error_log)

        # Verify if it contains the info we expect.
        self.assertIsNotNone(xml.find('./channel[@id="channel1.com"]'))
        self.assertIsNotNone(xml.find('./channel[@id="channel2.com"]'))
        self.assertIsNotNone(xml.find('./channel[@id="radio1.com"]'))
        self.assertIsNotNone(xml.find('./channel[@id="één.be"]'))
        self.assertIsNotNone(xml.find('./channel[@id="raw1.com"]'))
        self.assertIsNotNone(xml.find('./channel[@id="custom1.com"]'))
        self.assertIsNotNone(xml.find('./channel[@id="custom2.com"]'))
        self.assertIsNotNone(xml.find('./programme[@channel="channel1.com"]'))
        self.assertIsNotNone(xml.find('./programme[@channel="channel2.com"]'))
        self.assertIsNone(xml.find('./programme[@channel="radio1.com"]'))  # No epg for this channel
        self.assertIsNotNone(xml.find('./programme[@channel="één.be"]'))
        self.assertIsNotNone(xml.find('./programme[@channel="raw1.com"]'))
        self.assertIsNotNone(xml.find('./programme[@channel="custom1.com"]'))
        self.assertIsNotNone(xml.find('./programme[@channel="custom2.com"]'))

    def test_play_from_guide(self):
        """Play something from the guide."""
        sys.listitem = ListItem(label='Example Show [COLOR green]•[/COLOR][COLOR vod="plugin://plugin.video.example/play/something"][/COLOR]',
                                path='pvr://guide/0006/2020-05-23 11:35:00.epg')

        # Try to play it
        ContextMenu().play()

        # Check that something is playing
        player = xbmc.Player()
        self.assertTrue(self._wait_for_playing(player, 'something.mp4'))

        xbmc.executebuiltin('PlayerControl(Stop)')  # This is instant
        self.assertFalse(player.isPlaying())

    @staticmethod
    def _wait_for_playing(player, filename, timeout=3):
        """Wait until a file appears on the filesystem."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if player.isPlaying() and player.getPlayingFile() == filename:
                return True
            time.sleep(.1)
        return False


if __name__ == '__main__':
    unittest.main()
