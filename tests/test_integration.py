# -*- coding: utf-8 -*-
""" Tests for Integration """

# pylint: disable=invalid-name,missing-docstring,no-self-use

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import unittest

from resources.lib.modules.addon import Addon


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
        Addon.refresh(True)

        # Check that the files now exist
        for path in [m3u_path, epg_path]:
            self.assertTrue(os.path.exists(path), '%s does not exist' % path)

        with open(m3u_path, 'r') as fdesc:
            data = fdesc.read()
            self.assertTrue('#EXTM3U' in data)
            self.assertTrue('channel1.com' in data)
            self.assertTrue('radio1.com' in data)

        with open(epg_path, 'r') as fdesc:
            data = fdesc.read()
            self.assertTrue('channel1.com' in data)
            self.assertTrue('1987-06-15' in data)


if __name__ == '__main__':
    unittest.main()
