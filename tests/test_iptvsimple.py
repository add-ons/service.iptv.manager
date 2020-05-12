# -*- coding: utf-8 -*-
""" Tests for IPTV Simpled """

# pylint: disable=invalid-name,missing-docstring,no-self-use

from __future__ import absolute_import, division, print_function, unicode_literals

import unittest

from resources.lib.modules.iptvsimple import IptvSimple


class IptvSimpleTest(unittest.TestCase):
    """ IPTV Simple Tests """

    def test_setup(self):
        """ Test the setup of IPTV Simple (this will be mocked) """
        self.assertTrue(IptvSimple.setup())

    def test_restart(self):
        """ Test the restart of IPTV Simple (this will be mocked) """
        IptvSimple.restart_required = True
        IptvSimple.restart(force=True)

        self.assertFalse(IptvSimple.restart_required)


if __name__ == '__main__':
    unittest.main()
