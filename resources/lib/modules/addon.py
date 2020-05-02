# -*- coding: utf-8 -*-
""" Addon Module """

from __future__ import absolute_import, division, unicode_literals

import json
import logging
import os
import tempfile
import time

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
            if not channel.get('id') or not channel.get('name') or not channel.get('stream'):
                _LOGGER.warning('Skipping channel since it is incomplete: %s', channel)
                continue

            # Fix logo path to be absolute
            if channel.get('logo'):
                if not (channel.get('logo').startswith('http://') or channel.get('logo').startswith('https://') or channel.get('logo').startswith('special://')):
                    channel['logo'] = os.path.join(self.addon_path, channel.get('logo'))
            else:
                # TODO: use the logo of the addon
                pass

            channels.append(channel)

        return channels

    def get_epg(self):
        """ Get epg data from this add-on """
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

            # Make request
            _, temp_file = tempfile.mkstemp()
            uri = uri.replace('$FILE', temp_file)
            kodiutils.execute_builtin('RunPlugin', uri)

            # Wait for data
            self._wait_for_data(temp_file, 30)

            # Load data
            _LOGGER.info('Loading reply from %s', temp_file)
            with open(temp_file) as fdesc:
                data = json.load(fdesc)

            # Remove temp file
            os.unlink(temp_file)

            return data

        if uri.startswith('http://') or uri.startswith('https://'):
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
    def _wait_for_data(filename, timeout=60):
        """ Wait for data to arrive in the specified file """
        deadline = time.time() + timeout
        while time.time() < deadline:

            # Check if the file disappeared. This indicates that something went wrong.
            if not os.path.exists(filename):
                raise Exception('Error in other Add-on')

            # Check if the file got data. This indicates we have a result.
            if os.stat(filename).st_size > 0:
                return True

            # Wait a bit
            _LOGGER.debug('Waiting for %s... %s', filename, time.time())
            time.sleep(0.5)

        raise Exception('Timout waiting on reply from other Add-on')
