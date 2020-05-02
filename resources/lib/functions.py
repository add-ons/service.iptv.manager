# -*- coding: utf-8 -*-
""" Functions code """

from __future__ import absolute_import, division, unicode_literals

import logging

from resources.lib import kodilogging, kodiutils
from resources.lib.modules.iptvsimple import IptvSimple

kodilogging.config()
_LOGGER = logging.getLogger(__name__)


# TODO: throws the error:
# RuntimeError: No valid addon id could be obtained. None was passed and the script wasn't executed in a normal xbmc manner.


def setup_iptv_simple():
    """ Setup IPTV Simple """
    _LOGGER.warning('setup IPTV Simple')
    # TODO


def refresh():
    """ Refresh the channels and EPG """
    reply = kodiutils.yesno_dialog(message='Are you sure to setup IPTV Simple?')  # TODO: translation
    if reply:
        IptvSimple.setup()


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
