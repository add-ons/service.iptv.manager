# -*- coding: utf-8 -*-
"""Context Menu Module"""

from __future__ import absolute_import, division, unicode_literals

import logging
import re
import sys

from resources.lib import kodiutils

_LOGGER = logging.getLogger(__name__)


class ContextMenu:
    """ Helper class for PVR Context Menu handling (used in Kodi 18) """

    def __init__(self):
        """ Initialise object """

    def play(self):
        """ Play from Context Menu """
        stream = self.get_direct_uri()
        if stream is None:
            kodiutils.ok_dialog(message=kodiutils.localize(30706))
            return

        _LOGGER.debug('Playing using direct URI: %s', stream)
        kodiutils.execute_builtin('PlayMedia', stream)

    @staticmethod
    def get_direct_uri():
        """ Retrieve a direct URI from the selected ListItem. """
        # We use a clever way / ugly hack (pick your choice) to hide the direct stream in Kodi 18.
        # Title [COLOR green]•[/COLOR][COLOR vod="plugin://plugin.video.example/play/whatever"][/COLOR]
        label = sys.listitem.getLabel()  # pylint: disable=no-member
        stream = re.search(r'\[COLOR vod="([^"]+)"\]', label)
        return stream.group(1) if stream else None
