# -*- coding: utf-8 -*-
""" Tests for Integration """

# pylint: disable=invalid-name,missing-docstring,no-self-use

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import time
import unittest
from xml.etree import ElementTree as etree

from mock import patch

import xbmc

from resources.lib.modules.addon import Addon
from resources.lib.modules.contextmenu import ContextMenu
from tests.xbmc import to_unicode
from tests.xbmcgui import ListItem


class IntegrationTest(unittest.TestCase):
    """ Integration Tests """

    def test_refresh(self):
        """ Test the refreshing of data """
        m3u_path = 'tests/userdata/playlist.m3u8'
        epg_path = 'tests/userdata/epg.xml'

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
        with open(m3u_path, 'r') as fdesc:
            data = to_unicode(fdesc.read())
            self.assertTrue('#EXTM3U' in data)
            self.assertTrue('channel1.com' in data)
            self.assertTrue('radio1.com' in data)
            self.assertTrue('één.be' in data)

        # Validate EPG
        xml = etree.parse(epg_path)
        self.assertIsNotNone(xml.find('./channel[@id="channel1.com"]'))
        self.assertIsNotNone(xml.find('./channel[@id="één.be"]'))

        # Now, try playing something from the Guide
        import sys
        sys.listitem = ListItem(path='pvr://guide/0006/2020-05-23 11:35:00.epg')
        xbmc.INFO_LABELS.update({
            'ListItem.ChannelName': 'Channel 1',
            'ListItem.ChannelNumberLabel': 9,
            'ListItem.Date': '22-05-2020 18:15',
            'ListItem.EndTime': '19:15',
            'ListItem.Duration': '01:00:00',
            'ListItem.Title': 'Example Show',
            'ListItem.FolderPath': 'pvr://guide/0006/2020-05-23 11:35:00.epg',
        })

        # Get the current selected EPG item
        program = ContextMenu.get_selection()
        self.assertTrue(program)
        self.assertEqual(program.get('duration'), 3600)
        self.assertEqual(program.get('channel'), 'Channel 1')

        # Make sure we can detect that playback has started
        if os.path.exists('/tmp/playback-started.txt'):
            os.unlink('/tmp/playback-started.txt')

        with patch('xbmcgui.Dialog.select', return_value=0):
            # Try to play it
            ContextMenu.play(program)

        # Check that something has played
        self.assertTrue(self._wait_for_file('/tmp/playback-started.txt'))

        # Now, try playing something from the Guide but we moved our mouse...
        sys.listitem = ListItem(path='pvr://guide/0012/2020-05-24 12:00:00.epg')

        # Get the current selected EPG item, but the selected item is wrong.
        program = ContextMenu.get_selection()
        self.assertIsNone(program)

    @staticmethod
    def _wait_for_file(filename, timeout=10):
        """ Wait until a file appears on the filesystem. """
        deadline = time.time() + timeout
        while time.time() < deadline:
            if os.path.exists(filename):
                return True
            time.sleep(.1)
        return False


if __name__ == '__main__':
    unittest.main()
