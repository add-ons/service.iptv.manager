# -*- coding: utf-8 -*-
""" Functions code """

from __future__ import absolute_import, division, unicode_literals

import logging

from resources.lib import kodilogging, kodiutils
from resources.lib.modules.iptvsimple import IptvSimple

kodilogging.config()
_LOGGER = logging.getLogger(__name__)


def setup_iptv_simple():
    """ Setup IPTV Simple """
    reply = kodiutils.yesno_dialog(message=kodiutils.localize(30700))  # Are you sure...
    if reply:
        if IptvSimple.setup():
            kodiutils.ok_dialog(message=kodiutils.localize(30701))  # The configuration of IPTV Simple is completed!
        else:
            kodiutils.ok_dialog(message=kodiutils.localize(30702))  # The configuration of IPTV Simple has failed!


def refresh():
    """ Refresh the channels and EPG """
    _LOGGER.debug('TODO: refresh')


def run(function, *args):
    """ Run the function """
    function_map = {
        'setup-iptv-simple': setup_iptv_simple,
        'refresh': refresh,
    }
    try:
        # TODO: allow to pass *args to the function so we can also pass arguments
        _LOGGER.debug('Routing to function: %s', function)
        function_map.get(function)()
    except TypeError:
        _LOGGER.error('Could not route to %s', function)
        raise
