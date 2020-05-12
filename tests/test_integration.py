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
        epg_path = 'tests/userdata/epg.xml'
        m3u_path = 'tests/userdata/playlist.m3u8'

        # Remove existing files
        for path in [epg_path, m3u_path]:
            if os.path.exists(path):
                os.unlink(path)

        # Do the refresh
        Addon.refresh()

        # Check that the files now exist
        for path in [epg_path, m3u_path]:
            self.assertTrue(os.path.exists(path), '%s does not exist' % path)


if __name__ == '__main__':
    unittest.main()
