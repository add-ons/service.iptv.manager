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

    def __init__(self, addon_id, addon_obj, channels_uri, epg_uri):
        self.addon_id = addon_id
        self.addon_obj = addon_obj
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

            # Check if add-on supports IPTV Manager
            if addon.getSetting('iptv.enabled') != 'true':
                continue

            addons.append(Addon(
                addon_id=row['addonid'],
                addon_obj=addon,
                channels_uri=addon.getSetting('iptv.channels_uri'),
                epg_uri=addon.getSetting('iptv.epg_uri'),
            ))

        return addons

    def get_channels(self):
        """ Get channel data from this add-on """
        _LOGGER.info('Requesting channels from %s...', self.channels_uri)
        if not self.channels_uri:
            return {}

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

            # Add add-on name as group
            if not channel.get('group'):
                channel['group'] = kodiutils.addon_name(self.addon_obj)

            channels.append(channel)

        return channels

    def get_epg(self):
        """ Get epg data from this add-on """
        if not self.epg_uri:
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
            result = self._wait_for_data(sock)

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
    def _wait_for_data(sock, timeout=10):
        """ Wait for data to arrive on the socket """
        # Set a connection timeout
        # The remote and should connect back as soon as possible so we know that the request is being processed
        sock.settimeout(timeout)

        # Accept one client
        try:
            _LOGGER.debug('Waiting for a connection on port %s...', sock.getsockname()[1])
            conn, addr = sock.accept()
            _LOGGER.debug('Connected to %s:%s! Waiting for result...', addr[0], addr[1])

            # Read until the remote end closes the connection
            buffer = ''
            while True:
                chunk = conn.recv(1024)
                if not chunk:
                    break
                buffer += chunk

            if not buffer:
                # We got an empty reply, this means that something didn't go according to plan
                raise Exception('Something went wrong in the other Add-on')

            return buffer

        except socket.timeout:
            raise Exception('Timout waiting on reply from other Add-on')

        finally:
            # Close our socket
            _LOGGER.debug('Closing socket on port %s', sock.getsockname()[1])
            sock.close()
