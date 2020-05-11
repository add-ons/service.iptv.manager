# -*- coding: utf-8 -*-
""" Background service code """

from __future__ import absolute_import, division, unicode_literals

import logging
import time

from xbmc import Monitor

from resources.lib import kodilogging, kodiutils
from resources.lib.modules.addon import Addon

kodilogging.config()
_LOGGER = logging.getLogger(__name__)


class BackgroundService(Monitor):
    """ Background service code """

    def __init__(self):
        Monitor.__init__(self)

    def run(self):
        """ Background loop for maintenance tasks """
        _LOGGER.debug('Service started')

        # Do an initial update at startup
        Addon.refresh()

        # Service loop
        while not self.abortRequested():
            # Check if we need to do an update
            if self._is_update_required():
                Addon.refresh()

            # Stop when abort requested
            if self.waitForAbort(60):
                break

        _LOGGER.debug('Service stopped')

    @staticmethod
    def _is_update_required():
        """ Returns if we should trigger an update based on the settings. """
        refresh_interval = kodiutils.get_setting_int('refresh_interval') * 60 * 60
        last_updated = kodiutils.get_setting_int('last_updated', 0)
        _LOGGER.debug('last_updated = %d, time = %d, refresh_interval = %d', last_updated, time.time(), refresh_interval)
        return (last_updated + refresh_interval) <= time.time()


def run():
    """ Run the BackgroundService """
    BackgroundService().run()
