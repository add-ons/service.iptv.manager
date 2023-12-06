# -*- coding: utf-8 -*-
"""Sources Module"""

from __future__ import absolute_import, division, unicode_literals

import logging
import re
import time

import requests

from resources.lib import kodiutils
from resources.lib.modules.iptvsimple import IptvSimple

_LOGGER = logging.getLogger(__name__)


class Sources:
    """Helper class for Source updating"""

    def __init__(self):
        """ Initialise object """

    @classmethod
    def refresh(cls, show_progress=False):
        """Update channels and EPG data"""
        channels = []
        epg = []

        if show_progress:
            progress = kodiutils.progress(message=kodiutils.localize(30703))  # Detecting IPTV add-ons...
        else:
            progress = None

        from resources.lib.modules.sources.addon import AddonSource
        addon_sources = AddonSource.detect_sources()

        from resources.lib.modules.sources.external import ExternalSource
        external_sources = ExternalSource.detect_sources()

        sources = [source for source in addon_sources + external_sources if source.enabled]

        for index, source in enumerate(sources):
            # Skip Add-ons that have IPTV Manager support disabled
            if not source.enabled:
                continue

            _LOGGER.info('Updating IPTV data for %s...', source)

            if progress:
                # Fetching channels and guide of {addon}...
                progress.update(int(100 * index / len(sources)),
                                kodiutils.localize(30704).format(addon=str(source)))

            # Fetch channels
            channels.append(dict(
                name=str(source),
                channels=source.get_channels(),
            ))

            if progress and progress.iscanceled():
                progress.close()
                return

            # Fetch EPG
            epg.append(source.get_epg())

            if progress and progress.iscanceled():
                progress.close()
                return

        # Write files
        if show_progress:
            progress.update(100, kodiutils.localize(30705))  # Updating channels and guide...

        IptvSimple.write_playlist(channels)
        IptvSimple.write_epg(epg, channels)

        if kodiutils.get_setting_bool('iptv_simple_restart'):
            if show_progress:
                # Restart now.
                IptvSimple.restart(True)
            else:
                # Try to restart now. We will schedule it if the user is watching TV.
                IptvSimple.restart(False)

        # Update last_refreshed
        kodiutils.set_setting_int('last_refreshed', int(time.time()))

        if show_progress:
            progress.close()


class Source(object):  # pylint: disable=useless-object-inheritance
    """ Base class for a Source """

    def __init__(self):
        """ Initialise object """

    @staticmethod
    def detect_sources():
        """ Detect available sources. """
        raise NotImplementedError

    def enable(self):
        """ Enable this source. """
        raise NotImplementedError

    def disable(self):
        """ Disable this source. """
        raise NotImplementedError

    def get_channels(self):
        """ Get channel data from this source. """
        raise NotImplementedError

    @staticmethod
    def get_epg():
        """ Get EPG data from this source. """
        raise NotImplementedError

    def _load_url(self, url):
        """ Load the specified URL. """
        response = requests.get(url)
        response.raise_for_status()

        if url.lower().endswith('.gz'):
            return self._decompress_gz(response.content)
        if url.lower().endswith('.bz2'):
            return self._decompress_bz2(response.content)

        return response.text

    def _load_file(self, filename):
        """ Load the specified file. """
        with open(filename, 'rb') as fdesc:
            data = fdesc.read()

        if filename.lower().endswith('.gz'):
            return self._decompress_gz(data)
        if filename.lower().endswith('.bz2'):
            return self._decompress_bz2(data)

        return data.decode(encoding='utf-8')

    @staticmethod
    def _extract_m3u(data):
        """ Extract the m3u content """
        return data.replace('#EXTM3U', '').strip()

    @staticmethod
    def _extract_xmltv(data):
        """ Extract the xmltv content """
        return re.search(r'<tv[^>]*>(.*)</tv>', data, flags=re.DOTALL).group(1).strip()

    @staticmethod
    def _decompress_gz(data):
        """ Decompress gzip data. """
        try:  # Python 3
            from gzip import decompress
            return decompress(data).decode()
        except ImportError:  # Python 2
            from gzip import GzipFile

            from StringIO import StringIO
            with GzipFile(fileobj=StringIO(data)) as fdesc:
                return fdesc.read().decode()

    @staticmethod
    def _decompress_bz2(data):
        """ Decompress bzip2 data. """
        from bz2 import decompress
        return decompress(data).decode()
