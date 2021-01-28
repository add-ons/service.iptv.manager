# -*- coding: utf-8 -*-
"""Tests for Integration"""

# pylint: disable=invalid-name,missing-docstring,no-self-use

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import time
import unittest
from xml.etree import ElementTree as etree

import xbmc
from mock import patch
from xbmcgui import ListItem

from resources.lib import kodiutils
from resources.lib.modules.addon import Addon


class IntegrationTest(unittest.TestCase):
    """Integration Tests"""

    def test_refresh(self):
        """Test the refreshing of data"""
        m3u_path = 'tests/home/userdata/addon_data/service.iptv.manager/playlist.m3u8'
        epg_path = 'tests/home/userdata/addon_data/service.iptv.manager/epg.xml'

        # Remove existing files
        for path in [m3u_path, epg_path]:
            if os.path.exists(path):
                os.unlink(path)

        # Do the refresh
        with patch('xbmcgui.DialogProgress.iscanceled', return_value=False):
            Addon.refresh(True)

        # Check that the files now exist
        for path in [m3u_path, epg_path]:
            self.assertTrue(os.path.exists(path), '%s does not exist' % path)

        # Validate playlist
        with open(m3u_path, 'rb') as fdesc:
            data = kodiutils.to_unicode(fdesc.read())
            self.assertTrue('#EXTM3U' in data)
            self.assertTrue('channel1.com' in data)
            self.assertTrue('radio1.com' in data)
            self.assertTrue('één.be' in data)
            self.assertTrue('raw1.com' in data)
            self.assertTrue('#KODIPROP:inputstream=inputstream.ffmpegdirect' in data)

        # Validate EPG
        xml = etree.parse(epg_path)
        self.assertIsNotNone(xml.find('./channel[@id="channel1.com"]'))
        self.assertIsNotNone(xml.find('./channel[@id="één.be"]'))
        self.assertIsNotNone(xml.find('./channel[@id="raw1.com"]'))

        # Now, try playing something from the Guide
        import sys
        sys.listitem = ListItem(label='Example Show [COLOR green]•[/COLOR][COLOR vod="plugin://plugin.video.example/play/something"][/COLOR]',
                                path='pvr://guide/0006/2020-05-23 11:35:00.epg')

        # Try to play it
        from resources.lib.functions import play_from_contextmenu
        play_from_contextmenu()

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
