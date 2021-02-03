# -*- coding: utf-8 -*-
"""Sources Module"""

from __future__ import absolute_import, division, unicode_literals

import json
import logging
import os
import socket
import sys

from resources.lib import kodiutils
from resources.lib.modules.sources import Source

_LOGGER = logging.getLogger(__name__)


def update_qs(url, **params):
    """Add or update a URL query string"""
    try:  # Python 3
        from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
    except ImportError:  # Python 2
        from urllib import urlencode

        from urlparse import parse_qsl, urlparse, urlunparse
    url_parts = list(urlparse(url))
    query = dict(parse_qsl(url_parts[4]))
    query.update(params)
    url_parts[4] = urlencode(query)
    return urlunparse(url_parts)


class AddonSource(Source):
    """ Defines an Add-on source """

    CHANNELS_VERSION = 1
    EPG_VERSION = 1

    def __init__(self, addon_id, enabled=False, channels_uri=None, epg_uri=None):
        """ Initialise object """
        super(AddonSource, self).__init__()
        self.addon_id = addon_id
        self.enabled = enabled
        self.channels_uri = channels_uri
        self.epg_uri = epg_uri

        addon = kodiutils.get_addon(addon_id)
        self.addon_obj = addon
        self.addon_path = kodiutils.addon_path(addon)

    def __str__(self):
        return kodiutils.addon_name(self.addon_obj)

    @staticmethod
    def detect_sources():
        """ Find add-ons that provide IPTV channel data.

        :rtype: list[AddonSource]
        """
        result = kodiutils.jsonrpc(method="Addons.GetAddons",
                                   params={'installed': True, 'enabled': True, 'type': 'xbmc.python.pluginsource'})

        sources = []
        for row in result['result'].get('addons', []):
            addon = kodiutils.get_addon(row['addonid'])

            # Check if add-on supports IPTV Manager
            if not addon.getSetting('iptv.enabled'):
                continue

            sources.append(AddonSource(
                addon_id=row['addonid'],
                enabled=addon.getSetting('iptv.enabled') == 'true',
                channels_uri=addon.getSetting('iptv.channels_uri'),
                epg_uri=addon.getSetting('iptv.epg_uri'),
            ))

        return sources

    def enable(self):
        """ Enable this source. """
        addon = kodiutils.get_addon(self.addon_id)
        addon.setSetting('iptv.enabled', 'true')

    def disable(self):
        """ Disable this source. """
        addon = kodiutils.get_addon(self.addon_id)
        addon.setSetting('iptv.enabled', 'false')

    def get_channels(self):
        """ Get channel data from this source.

        :rtype: dict|str
        """
        _LOGGER.info('Requesting channels from %s...', self.channels_uri)
        if not self.channels_uri:
            return []

        try:
            data = self._get_data_from_addon(self.channels_uri)
            _LOGGER.debug(data)
        except Exception as exc:  # pylint: disable=broad-except
            _LOGGER.error('Something went wrong while calling %s: %s', self.addon_id, exc)
            return []

        # Return M3U8-format as-is without headers
        if not isinstance(data, dict):
            return self._extract_m3u(data)

        # JSON-STREAMS format
        if data.get('version', 1) > self.CHANNELS_VERSION:
            _LOGGER.warning('Skipping %s since it uses an unsupported version: %d', self.channels_uri,
                            data.get('version'))
            return []

        channels = []
        for channel in data.get('streams', []):
            # Check for required fields
            if not channel.get('name') or not channel.get('stream'):
                _LOGGER.warning('Skipping channel since it is incomplete: %s', channel)
                continue

            # Fix logo path to be absolute
            if not channel.get('logo'):
                channel['logo'] = kodiutils.addon_icon(self.addon_obj)
            elif not channel.get('logo').startswith(('http://', 'https://', 'special://', 'resource://', '/')):
                channel['logo'] = os.path.join(self.addon_path, channel.get('logo'))

            # Ensure group is a set
            if not channel.get('group'):
                channel['group'] = set()
            # Accept string values (backward compatible)
            elif isinstance(channel.get('group'), (bytes, str)):
                channel['group'] = set(channel.get('group').split(';'))
            # Accept string values (backward compatible, py2 version)
            elif sys.version_info.major == 2 and isinstance(channel.get('group'), unicode): # noqa: F821; pylint: disable=undefined-variable
                channel['group'] = set(channel.get('group').split(';'))
            elif isinstance(channel.get('group'), list):
                channel['group'] = set(list(channel.get('group')))
            else:
                _LOGGER.warning('Channel group is not a list: %s', channel)
                channel['group'] = set()
            # Add add-on name as group, if not already
            channel['group'].add(kodiutils.addon_name(self.addon_obj))

            channels.append(channel)

        return channels

    def get_epg(self):
        """ Get EPG data from this source.

        :rtype: dict|str
        """
        if not self.epg_uri:
            return {}

        _LOGGER.info('Requesting epg from %s...', self.epg_uri)
        try:
            data = self._get_data_from_addon(self.epg_uri)
        except Exception as exc:  # pylint: disable=broad-except
            _LOGGER.error('Something went wrong while calling %s: %s', self.addon_id, exc)
            return {}

        # Return XMLTV-format as-is without headers and footers
        if not isinstance(data, dict):
            return self._extract_xmltv(data)

        # JSON-EPG format
        if data.get('version', 1) > self.EPG_VERSION:
            _LOGGER.warning('Skipping EPG from %s since it uses an unsupported version: %d', self.epg_uri,
                            data.get('version'))
            return {}

        # Check for required fields
        if not data.get('epg'):
            _LOGGER.warning('Skipping EPG from %s since it is incomplete', self.epg_uri)
            return {}

        return data['epg']

    def _get_data_from_addon(self, uri):
        """ Request data from the specified URI. """
        # Plugin path
        if uri.startswith('plugin://'):
            # Prepare data
            sock = self._prepare_for_data()
            uri = update_qs(uri, port=sock.getsockname()[1])

            _LOGGER.info('Executing RunPlugin(%s)...', uri)
            kodiutils.execute_builtin('RunPlugin', uri)

            # Wait for data
            result = self._wait_for_data(sock)

            # Load data
            data = json.loads(result)

            return data

        # Currently, only plugin:// uris are supported
        raise NotImplementedError

    @staticmethod
    def _prepare_for_data():
        """ Prepare ourselves so we can receive data. """
        # Bind on localhost on a free port above 1024
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('localhost', 0))

        _LOGGER.debug('Bound on port %s...', sock.getsockname()[1])

        # Listen for one connection
        sock.listen(1)
        return sock

    def _wait_for_data(self, sock, timeout=10):
        """ Wait for data to arrive on the socket. """
        # Set a connection timeout
        # The remote and should connect back as soon as possible so we know that the request is being processed
        sock.settimeout(timeout)

        try:
            _LOGGER.debug('Waiting for a connection from %s on port %s...', self.addon_id, sock.getsockname()[1])

            # Accept one client
            conn, addr = sock.accept()
            _LOGGER.debug('Connected to %s:%s! Waiting for result...', addr[0], addr[1])

            # We have no timeout when the connection is established
            conn.settimeout(None)

            # Read until the remote end closes the connection
            buf = ''
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                buf += chunk.decode()

            if not buf:
                # We got an empty reply, this means that something didn't go according to plan
                raise Exception('Something went wrong in %s' % self.addon_id)

            return buf

        except socket.timeout:
            raise Exception('Timout waiting for reply on port %s' % sock.getsockname()[1])

        finally:
            # Close our socket
            _LOGGER.debug('Closing socket on port %s', sock.getsockname()[1])
            sock.close()
