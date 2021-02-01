# -*- coding: utf-8 -*-
"""Sources Module"""

from __future__ import absolute_import, division, unicode_literals

import json
import logging
import os

from resources.lib import kodiutils
from resources.lib.modules.sources import Source

_LOGGER = logging.getLogger(__name__)


class ExternalSource(Source):
    """ Defines an External source """

    SOURCES_FILE = 'sources.json'

    TYPE_NONE = 0
    TYPE_URL = 1
    TYPE_FILE = 2

    def __init__(self, uuid, name, enabled, playlist_uri=None, playlist_type=TYPE_NONE, epg_uri=None, epg_type=TYPE_NONE):
        """ Initialise object """
        super(ExternalSource, self).__init__()
        self.uuid = uuid
        self.name = name
        self.enabled = enabled
        self.playlist_uri = playlist_uri
        self.playlist_type = playlist_type
        self.epg_uri = epg_uri
        self.epg_type = epg_type

    def __str__(self):
        return self.name

    @staticmethod
    def detect_sources():
        """ Load our sources that provide external channel data.

        :rtype: list[ExternalSource]
        """
        try:
            with open(os.path.join(kodiutils.addon_profile(), ExternalSource.SOURCES_FILE), 'r') as fdesc:
                result = json.loads(fdesc.read())
        except (IOError, TypeError, ValueError):
            result = {}

        sources = []
        for source in result.values():
            sources.append(ExternalSource(
                uuid=source.get('uuid'),
                name=source.get('name'),
                enabled=source.get('enabled'),
                playlist_uri=source.get('playlist_uri'),
                playlist_type=source.get('playlist_type', ExternalSource.TYPE_NONE),
                epg_uri=source.get('epg_uri'),
                epg_type=source.get('epg_type', ExternalSource.TYPE_NONE),
            ))

        return sources

    def enable(self):
        """ Enable this source. """
        self.enabled = True
        self.save()

    def disable(self):
        """ Disable this source. """
        self.enabled = False
        self.save()

    def get_channels(self):
        """ Get channel data from this source.

        :rtype: str
        """
        if self.playlist_type == self.TYPE_NONE:
            return ''

        if self.playlist_type == self.TYPE_FILE:
            data = self._load_file(self.playlist_uri)
        elif self.playlist_type == self.TYPE_URL:
            data = self._load_url(self.playlist_uri)
        else:
            raise ValueError('Unknown source type: %s' % self.playlist_type)

        return self._extract_m3u(data)  # Remove the headers

    def get_epg(self):
        """ Get EPG data from this source.

        :rtype: str
        """
        if self.epg_type == self.TYPE_NONE:
            return ''

        if self.epg_type == self.TYPE_FILE:
            data = self._load_file(self.epg_uri)
        elif self.epg_type == self.TYPE_URL:
            data = self._load_url(self.epg_uri)
        else:
            raise ValueError('Unknown source type: %s' % self.epg_type)

        return self._extract_xmltv(data)  # Remove the headers

    def save(self):
        """ Save this source. """
        output_path = kodiutils.addon_profile()
        try:
            if not os.path.exists(output_path):
                os.mkdir(output_path)

            with open(os.path.join(output_path, ExternalSource.SOURCES_FILE), 'r') as fdesc:
                sources = json.loads(fdesc.read())
        except (IOError, TypeError, ValueError):
            sources = {}

        # Update the element with my uuid
        sources[self.uuid] = self.__dict__

        with open(os.path.join(output_path, ExternalSource.SOURCES_FILE), 'w') as fdesc:
            json.dump(sources, fdesc)

    def delete(self):
        """ Delete this source. """
        output_path = kodiutils.addon_profile()
        try:
            with open(os.path.join(output_path, ExternalSource.SOURCES_FILE), 'r') as fdesc:
                sources = json.loads(fdesc.read())
        except (IOError, TypeError, ValueError):
            sources = {}

        # Remove the element with my uuid
        sources.pop(self.uuid)

        with open(os.path.join(output_path, ExternalSource.SOURCES_FILE), 'w') as fdesc:
            json.dump(sources, fdesc)
