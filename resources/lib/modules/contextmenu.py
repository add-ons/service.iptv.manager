# -*- coding: utf-8 -*-
""" Addon Module """

from __future__ import absolute_import, division, unicode_literals

import json
import logging
import os
import sys
import time
from datetime import datetime

from resources.lib import kodiutils

_LOGGER = logging.getLogger(__name__)

CHANNELS_CACHE = 'channels.json'


class ContextMenu:
    """Helper class for PVR Context Menu handling"""

    def __init__(self):
        """Initialise the Context Menu Module"""

    @classmethod
    def play(cls, program):
        """Play the selected program."""
        _LOGGER.debug('Playing %s', program)

        # Get a list of addons that can play the selected channel
        # We do the lookup based on Channel Name, since that's all we have
        addons = cls._get_addons_for_channel(program.get('channel'))

        if not addons:
            # Channel was not found.
            _LOGGER.debug('No Add-on was found to play %s', program.get('channel'))
            kodiutils.notification(message=kodiutils.localize(30710, channel=program.get('channel')))  # Could not find an Add-on...
            return

        if len(addons) == 1:
            # Channel has one Add-on. Play it directly.
            _LOGGER.debug('One Add-on was found to play %s: %s', program.get('channel'), addons)
            cls._play(addons.values()[0], program)
            return

        # Ask the user to pick an Add-on
        _LOGGER.debug('Multiple Add-on were found to play %s: %s', program.get('channel'), addons)
        addons_list = list(addons)
        ret = kodiutils.select(heading=kodiutils.localize(30711), options=addons_list)  # Select an Add-on...
        if ret == -1:
            _LOGGER.debug('The selection to play an item from %s was canceled', program.get('channel'))
            return

        cls._play(addons.get(addons_list[ret]), program)

    @classmethod
    def _play(cls, uri, program):
        """Play the selected program with the specified URI."""
        if '{date}' in uri:
            uri = uri.format(date=program.get('start').isoformat())

        if '{duration}' in uri:
            uri = uri.format(date=program.get('duration').isoformat())

        _LOGGER.debug('Playing "%s"', uri)
        kodiutils.execute_builtin('PlayMedia', uri)

    @classmethod
    def get_selection(cls):
        """Retrieve information about the selected ListItem."""

        # The selected ListItem should be in sys.listitem, but I could not find real data in there that we can use for EPG selections.
        # Therefore, we use xbmc.getInfoLabel(ListItem.xxx), but that references the currently selected ListItem. This could not be the same as the
        # item where the Context Menu was opened on, when the selection was moved really quick before the Python code was started.
        # It seems I'm not alone in this: https://forum.kodi.tv/showthread.php?tid=294357

        # cls._debug_get_selection()

        # Check if the selected item is also the intended item
        if sys.listitem.getPath() != kodiutils.get_info_label('ListItem.FolderPath'):  # pylint: disable=no-member
            # We are in trouble. We know that the data we want to use is invalid, but there is nothing we can do.
            kodiutils.ok_dialog(message=kodiutils.localize(30712))  # Could not determine the selected program...
            return None

        # Load information from the ListItem
        date = kodiutils.get_info_label('ListItem.Date')
        duration = kodiutils.get_info_label('ListItem.Duration')
        channel = kodiutils.to_unicode(kodiutils.get_info_label('ListItem.ChannelName'))

        # Parse begin to a datetime
        date_format = kodiutils.get_region('dateshort')
        try:
            start = datetime.strptime(date, date_format + ' %H:%M')
        except TypeError:
            start = datetime(*(time.strptime(date, date_format + ' %H:%M')[0:6]))

        # Parse duration to seconds
        splitted = duration.split(':')
        if len(splitted) == 1:  # %S
            seconds = int(splitted[0])

        elif len(splitted) == 2:  # %M:%S
            seconds = int(splitted[0]) * 60 + int(splitted[1])

        elif len(splitted) == 3:  # %H:%M:%S
            seconds = int(splitted[0]) * 3600 + int(splitted[1]) * 60 + int(splitted[2])

        else:
            raise Exception('Unknown duration %s' % duration)

        return dict(
            start=start,
            duration=seconds,
            channel=channel,
        )

    @staticmethod
    def write_channels(channels):
        """Write the channel data to a file."""
        channels_path = os.path.join(kodiutils.addon_profile(), CHANNELS_CACHE)
        with open(channels_path, 'w') as fdesc:
            json.dump(channels, fdesc)

    @staticmethod
    def _get_addons_for_channel(channel):
        """Returns a list of Add-ons that can play this channel."""
        channels_path = os.path.join(kodiutils.addon_profile(), CHANNELS_CACHE)
        with open(channels_path, 'r') as fdesc:
            data = json.load(fdesc)

        matches = {}
        for _addon in data:
            for _channel in _addon.get('channels', []):
                if _channel.get('name').lower() == channel.lower() and _channel.get('vod') is not None:
                    matches.update({_addon.get('addon_name'): _channel.get('vod')})

        return matches

    @staticmethod
    def _debug_get_selection():
        """Return debugging data for getting the current ListItem"""
        sys_listitem = sys.listitem  # pylint: disable=no-member
        # Show the data we can get from sys_listitem. This is the item where the context menu was opened on.
        _LOGGER.debug('sys.listitem.getLabel() = %s', sys_listitem.getLabel())
        _LOGGER.debug('sys.listitem.getLabel2() = %s', sys_listitem.getLabel2())
        _LOGGER.debug('sys.listitem.getfilename() = %s', sys_listitem.getfilename())  # inconsistent case
        _LOGGER.debug('sys.listitem.getPath() = %s', sys_listitem.getPath())
        _LOGGER.debug('sys.listitem.getArt("thumb") = %s', sys_listitem.getArt('thumb'))
        _LOGGER.debug('sys.listitem.getArt("poster") = %s', sys_listitem.getArt('poster'))
        _LOGGER.debug('sys.listitem.getArt("banner") = %s', sys_listitem.getArt('banner'))
        _LOGGER.debug('sys.listitem.getArt("fanart") = %s', sys_listitem.getArt('fanart'))
        _LOGGER.debug('sys.listitem.getArt("clearart") = %s', sys_listitem.getArt('clearart'))
        _LOGGER.debug('sys.listitem.getArt("clearlogo") = %s', sys_listitem.getArt('clearlogo'))
        _LOGGER.debug('sys.listitem.getArt("landscape") = %s', sys_listitem.getArt('landscape'))
        _LOGGER.debug('sys.listitem.getArt("icon") = %s', sys_listitem.getArt('icon'))
        _LOGGER.debug('sys.listitem.isSelected() = %s', sys_listitem.isSelected())

        for prop in ['id', 'dbid', 'AspectRatio', 'Date', 'fanart_image']:
            _LOGGER.debug('sys.listitem.getProperty("%s") = %s', prop, sys_listitem.getProperty(prop))

        _LOGGER.debug('sys.listitem.getVideoInfoTag().getCast() = %s', sys_listitem.getVideoInfoTag().getCast())
        _LOGGER.debug('sys.listitem.getVideoInfoTag().getDbId() = %s', sys_listitem.getVideoInfoTag().getDbId())
        _LOGGER.debug('sys.listitem.getVideoInfoTag().getDirector() = %s', sys_listitem.getVideoInfoTag().getDirector())
        _LOGGER.debug('sys.listitem.getVideoInfoTag().getFile() = %s', sys_listitem.getVideoInfoTag().getFile())
        _LOGGER.debug('sys.listitem.getVideoInfoTag().getFirstAired() = %s', sys_listitem.getVideoInfoTag().getFirstAired())
        _LOGGER.debug('sys.listitem.getVideoInfoTag().getIMDBNumber() = %s', sys_listitem.getVideoInfoTag().getIMDBNumber())
        _LOGGER.debug('sys.listitem.getVideoInfoTag().getLastPlayed() = %s', sys_listitem.getVideoInfoTag().getLastPlayed())
        _LOGGER.debug('sys.listitem.getVideoInfoTag().getMediaType() = %s', sys_listitem.getVideoInfoTag().getMediaType())
        _LOGGER.debug('sys.listitem.getVideoInfoTag().getOriginalTitle() = %s', sys_listitem.getVideoInfoTag().getOriginalTitle())
        _LOGGER.debug('sys.listitem.getVideoInfoTag().getPath() = %s', sys_listitem.getVideoInfoTag().getPath())
        _LOGGER.debug('sys.listitem.getVideoInfoTag().getPictureURL() = %s', sys_listitem.getVideoInfoTag().getPictureURL())
        _LOGGER.debug('sys.listitem.getVideoInfoTag().getPlayCount() = %s', sys_listitem.getVideoInfoTag().getPlayCount())
        _LOGGER.debug('sys.listitem.getVideoInfoTag().getPlot() = %s', sys_listitem.getVideoInfoTag().getPlot())
        _LOGGER.debug('sys.listitem.getVideoInfoTag().getPlotOutline() = %s', sys_listitem.getVideoInfoTag().getPlotOutline())
        _LOGGER.debug('sys.listitem.getVideoInfoTag().getPremiered() = %s', sys_listitem.getVideoInfoTag().getPremiered())
        _LOGGER.debug('sys.listitem.getVideoInfoTag().getRating() = %s', sys_listitem.getVideoInfoTag().getRating())
        _LOGGER.debug('sys.listitem.getVideoInfoTag().getTagLine() = %s', sys_listitem.getVideoInfoTag().getTagLine())
        _LOGGER.debug('sys.listitem.getVideoInfoTag().getTitle() = %s', sys_listitem.getVideoInfoTag().getTitle())
        _LOGGER.debug('sys.listitem.getVideoInfoTag().getTVShowTitle() = %s', sys_listitem.getVideoInfoTag().getTVShowTitle())
        _LOGGER.debug('sys.listitem.getVideoInfoTag().getVotes() = %s', sys_listitem.getVideoInfoTag().getVotes())
        _LOGGER.debug('sys.listitem.getVideoInfoTag().getYear() = %s', sys_listitem.getVideoInfoTag().getYear())

        # Show the data we can get from xmbc.getInfoLabel.  This is the item that is currently focused.
        items = [
            'ListItem.Thumb',
            'ListItem.Icon',
            'ListItem.Overlay',
            'ListItem.Tag',
            'ListItem.HasEPG',
            'ListItem.HasArchive',
            'ListItem.EpgEventTitle',
            'ListItem.EpgEventIcon',
            'ListItem.ChannelName',
            'ListItem.ChannelGroup',
            'ListItem.ChannelNumberLabel',
            'ListItem.Date',
            'ListItem.Duration',
            'ListItem.EndDate',
            'ListItem.EndTime',
            'ListItem.EpisodeName',
            'ListItem.FileName',
            'ListItem.FolderPath',
            'ListItem.Genre',
            'ListItem.Label',
            'ListItem.Path',
            'ListItem.Plot',
            'ListItem.PlotOutline',
            'ListItem.StartDate',
            'ListItem.StartTime',
            'ListItem.Title',
        ]
        for item in items:
            _LOGGER.debug('xmbc.getInfoLabel("%s") = %s', item, kodiutils.to_unicode(kodiutils.get_info_label(item)))
