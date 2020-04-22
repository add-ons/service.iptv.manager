# -*- coding: utf-8 -*-
""" Background service code """

from __future__ import absolute_import, division, unicode_literals

import logging

from xbmc import Monitor

from resources.lib import kodilogging
from resources.lib.modules.addon import Addon
from resources.lib.modules.iptvsimple import IptvSimple

kodilogging.config()
_LOGGER = logging.getLogger(__name__)


class BackgroundService(Monitor):
    """ Background service code """

    def __init__(self):
        Monitor.__init__(self)

    def run(self):
        """ Background loop for maintenance tasks """
        _LOGGER.info('Service started')

        # Configure IPTV Simple
        # TODO: we probably don't have to do this every time, or maybe only check if the configuration is wrong
        IptvSimple.setup()

        # Do an initial update
        # TODO: we have to schedule this somehow
        self.update()

        while not self.abortRequested():
            # Stop when abort requested
            if self.waitForAbort(10):
                break

        _LOGGER.info('Service stopped')

    @staticmethod
    def update():
        """ Update the channels and epg data """
        channels = []
        epg = dict()

        addons = Addon.get_iptv_addons()
        for addon in addons:
            _LOGGER.info('Updating IPTV data for %s...', addon.addon_id)

            # Fetch channels
            channels.extend(addon.get_channels())

            # Fetch EPG data
            epg.update(addon.get_epg())

        # Write files
        IptvSimple.write_playlist(channels)
        IptvSimple.write_epg(epg)

        IptvSimple.restart()


def run():
    """ Run the BackgroundService """
    BackgroundService().run()
