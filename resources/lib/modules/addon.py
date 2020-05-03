# -*- coding: utf-8 -*-
""" Addon Module """

from __future__ import absolute_import, division, unicode_literals

import json
import logging
import os
import socket

from resources.lib import kodiutils

_LOGGER = logging.getLogger(__name__)

IPTV_FILENAME = 'iptv.json'
IPTV_VERSION = 1
CHANNELS_VERSION = 1
EPG_VERSION = 1


class Addon:
    """ Helper class for Addon communication """

    def __init__(self, addon_id, channels_uri, epg_uri):
        self.addon_id = addon_id
        self.channels_uri = channels_uri
        self.epg_uri = epg_uri

        addon = kodiutils.get_addon(addon_id)
        self.addon_path = kodiutils.addon_path(addon)

    @staticmethod
    def get_iptv_addons():
        """ Find add-ons that provide IPTV channel data """
        result = kodiutils.jsonrpc(method="Addons.GetAddons", params={'installed': True, 'enabled': True, 'type': 'xbmc.python.pluginsource'})

        addons = []
        for row in result['result']['addons']:
            addon = kodiutils.get_addon(row['addonid'])
            addon_path = kodiutils.addon_path(addon)
            addon_iptv_config = os.path.join(addon_path, IPTV_FILENAME)

            # Check if this addon has an iptv.json
            if not os.path.exists(addon_iptv_config):
                continue

            # Read iptv.json
            with open(addon_iptv_config) as fdesc:
                data = json.load(fdesc)

            # Check version
            if data.get('version', 1) > IPTV_VERSION:
                _LOGGER.warning('Skipping %s since it uses an unsupported version of iptv.json: %d', row['addonid'], data.get('version'))
                continue

            if not data.get('channels'):
                _LOGGER.warning('Skipping %s since it has no channels defined', row['addonid'])
                continue

            addons.append(Addon(
                addon_id=row['addonid'],
                channels_uri=data.get('channels'),
                epg_uri=data.get('epg'),
            ))

        return addons

    def get_channels(self):
        """ Get channel data from this add-on """
        _LOGGER.info('Requesting channels from %s...', self.channels_uri)
        try:
            data = self._get_data_from_addon(self.channels_uri)
            _LOGGER.debug(data)
        except Exception as exc:  # pylint: disable=broad-except
            _LOGGER.error('Something went wrong while calling %s: %s', self.addon_id, exc)
            return []

        if data.get('version', 1) > CHANNELS_VERSION:
            _LOGGER.warning('Skipping %s since it uses an unsupported version: %d', self.channels_uri, data.get('version'))
            return []

        channels = []
        for channel in data.get('streams', []):
            # Check for required fields
            if not channel.get('name') or not channel.get('stream'):
                _LOGGER.warning('Skipping channel since it is incomplete: %s', channel)
                continue

            # Fix logo path to be absolute
            if channel.get('logo'):
                if not channel.get('logo').startswith(('http://', 'https://', 'special://', '/')):
                    channel['logo'] = os.path.join(self.addon_path, channel.get('logo'))
            else:
                # TODO: use the logo of the addon
                pass

            channels.append(channel)

        return channels

    def get_epg(self):
        """ Get epg data from this add-on """
        if self.epg_uri is None:
            return {}

        _LOGGER.info('Requesting epg from %s...', self.epg_uri)
        try:
            data = self._get_data_from_addon(self.epg_uri)
            _LOGGER.debug(data)
        except Exception as exc:  # pylint: disable=broad-except
            _LOGGER.error('Something went wrong while calling %s: %s', self.addon_id, exc)
            return {}

        if data.get('version', 1) > CHANNELS_VERSION:
            _LOGGER.warning('Skipping EPG from %s since it uses an unsupported version: %d', self.epg_uri, data.get('version'))
            return {}

        # Check for required fields
        if not data.get('epg'):
            _LOGGER.warning('Skipping EPG from %s since it is incomplete', self.epg_uri)
            return {}

        return data['epg']

    def _get_data_from_addon(self, uri):
        """ Request data from the specified URI """
        if uri.startswith('plugin://'):
            # Plugin path

            # Prepare data
            sock = self._prepare_for_data()
            uri = uri.replace('$PORT', str(sock.getsockname()[1]))

            _LOGGER.info('Executing RunPlugin(%s)...', uri)
            kodiutils.execute_builtin('RunPlugin', uri)

            # Wait for data
            result = self._wait_for_data(sock, 30)

            # Load data
            data = json.loads(result)

            return data

        if uri.startswith(('http://', 'https://')):
            # HTTP(S) path
            # TODO: implement requests to fetch data
            return None

        # Local path
        addon = kodiutils.get_addon(self.addon_id)
        addon_path = kodiutils.addon_path(addon)
        filename = os.path.join(addon_path, uri)

        if not os.path.exists(filename):
            raise Exception('File %s does not exist' % filename)

        # Read file
        _LOGGER.info('Loading fixed reply from %s', filename)
        with open(filename) as fdesc:
            data = json.load(fdesc)

        return data

    @staticmethod
    def _prepare_for_data():
        """ Prepare ourselves so we can receive data """
        # Bind on localhost on a free port above 1024
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('localhost', 0))

        _LOGGER.debug('Bound on port %s...', sock.getsockname()[1])

        # Listen for one connection
        sock.listen(1)
        return sock

    @staticmethod
    def _wait_for_data(sock, timeout=60):
        """ Wait for data to arrive on the socket """
        # Set our timeout
        sock.settimeout(timeout)

        # Accept one client
        try:
            _LOGGER.debug('Waiting for a connection on port %s...', sock.getsockname()[1])
            conn, addr = sock.accept()

            # Read until eof
            _LOGGER.debug('Connected to %s:%s! Reading result...', addr[0], addr[1])
            buffer = ''
            while True:
                chunk = conn.recv(65535)
                if not chunk:
                    break
                buffer += chunk

            return buffer

        except socket.timeout:
            raise Exception('Timout waiting on reply from other Add-on')

        finally:
            # Close our socket
            sock.close()

