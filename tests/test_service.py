# -*- coding: utf-8 -*-
""" Tests for background service """

# pylint: disable=invalid-name,missing-docstring

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import signal
import sys
import threading
import time
import unittest

import pytest

from resources.lib.service import BackgroundService


@unittest.skipIf(sys.platform.startswith("win"), 'Skipping on Windows.')
class TestService(unittest.TestCase):
    """ Tests for the background service """

    @staticmethod
    @pytest.mark.timeout(timeout=10, method='thread')
    def test_service():
        """ Run the background service for 5 seconds. It will raise an error when it doesn't stop after 10 seconds. """

        def terminate_service(seconds=5):
            """ Sleep a bit, and send us a SIGINT signal. """
            time.sleep(seconds)
            os.kill(os.getpid(), signal.SIGINT)

        threading.Thread(target=terminate_service).start()

        service = BackgroundService()
        service.run()


if __name__ == '__main__':
    unittest.main()
