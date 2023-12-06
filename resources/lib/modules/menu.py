# -*- coding: utf-8 -*-
""" Menu module """

from __future__ import absolute_import, division, unicode_literals

import logging
import os
from uuid import uuid4

from resources.lib import kodiutils
from resources.lib.kodiutils import TitleItem
from resources.lib.modules.iptvsimple import IPTV_SIMPLE_EPG, IPTV_SIMPLE_PLAYLIST, IptvSimple
from resources.lib.modules.sources import Sources
from resources.lib.modules.sources.addon import AddonSource
from resources.lib.modules.sources.external import ExternalSource

_LOGGER = logging.getLogger(__name__)


class Menu:
    """ Menu code """

    def __init__(self):
        """ Initialise object """

    @staticmethod
    def show_mainmenu():
        """ Show the main menu. """
        listing = []

        if not IptvSimple.check():
            listing.append(TitleItem(
                title='[B]%s[/B]' % kodiutils.localize(30001),  # Configure IPTV Simple automatically…
                path=kodiutils.url_for('install'),
                art_dict=dict(
                    icon='DefaultAddonService.png',
                ),
            ))

        listing.append(TitleItem(
            title=kodiutils.localize(30002),
            path=kodiutils.url_for('refresh'),  # Refresh channels and guide now…
            art_dict=dict(
                icon='DefaultAddonsUpdates.png',
            ),
        ))

        listing.append(TitleItem(
            title=kodiutils.localize(30003),  # IPTV Manager Settings…
            path=kodiutils.url_for('show_settings'),
            art_dict=dict(
                icon='DefaultAddonService.png',
            ),
            info_dict=dict(
                plot=kodiutils.localize(30003),  # IPTV Manager Settings…
            ),
        ))

        listing.append(TitleItem(
            title=kodiutils.localize(30004),  # Manage sources…
            path=kodiutils.url_for('show_sources'),
            art_dict=dict(
                icon='DefaultPlaylist.png',
            ),
            info_dict=dict(
                plot=kodiutils.localize(30004),  # Manage sources…
            ),
        ))

        kodiutils.show_listing(listing, sort=['unsorted'])

    @staticmethod
    def show_install():
        """ Setup IPTV Simple """
        reply = kodiutils.yesno_dialog(message=kodiutils.localize(30700))  # Are you sure...
        if reply:
            if IptvSimple.setup():
                kodiutils.ok_dialog(message=kodiutils.localize(30701))  # The configuration of IPTV Simple is completed!
            else:
                kodiutils.ok_dialog(message=kodiutils.localize(30702))  # The configuration of IPTV Simple has failed!
        kodiutils.end_of_directory()

    @staticmethod
    def show_settings():
        """ Show the sources menu. """
        kodiutils.open_settings()

    @staticmethod
    def refresh():
        """ Manually refresh to channels and epg. """
        kodiutils.end_of_directory()
        Sources.refresh(True)

    @staticmethod
    def show_sources():
        """ Show the sources menu. """
        listing = []

        addon_sources = AddonSource.detect_sources()
        external_sources = ExternalSource.detect_sources()

        if addon_sources:
            listing.append(TitleItem(
                title='[B]%s[/B]' % kodiutils.localize(30011),  # Supported Add-ons
                path=None,
                art_dict=dict(
                    icon='empty.png',
                ),
            ))
            for addon in addon_sources:
                if addon.enabled:
                    path = kodiutils.url_for('disable_source', addon_id=addon.addon_id)
                else:
                    path = kodiutils.url_for('enable_source', addon_id=addon.addon_id)

                listing.append(TitleItem(
                    title=kodiutils.addon_name(addon.addon_obj),
                    path=path,
                    art_dict=dict(
                        icon='icons/infodialogs/enabled.png' if addon.enabled else 'icons/infodialogs/disable.png',
                        poster=kodiutils.addon_icon(addon.addon_obj),
                    ),
                ))

        listing.append(TitleItem(
            title='[B]%s[/B]' % kodiutils.localize(30012),  # External Sources
            path=None,
            art_dict=dict(
                icon='empty.png',
            ),
        ))

        for source in external_sources:
            context_menu = [(
                kodiutils.localize(30014),  # Delete this Source
                'Container.Update(%s)' %
                kodiutils.url_for('delete_source', uuid=source.uuid)
            )]

            listing.append(TitleItem(
                title=source.name,
                path=kodiutils.url_for('edit_source', uuid=source.uuid),
                art_dict=dict(
                    icon='icons/infodialogs/enabled.png' if source.enabled else 'icons/infodialogs/disable.png',
                    poster='DefaultAddonService.png',
                ),
                context_menu=context_menu,
            ))

        listing.append(TitleItem(
            title=kodiutils.localize(30013),  # Add Source
            path=kodiutils.url_for('add_source'),
            art_dict=dict(
                icon='DefaultAddSource.png',
            ),
        ))

        kodiutils.show_listing(listing, category='Sources', sort=['unsorted'])

    @staticmethod
    def enable_addon_source(addon_id):
        """ Enable the specified source. """
        source = AddonSource(addon_id=addon_id)
        source.enable()
        kodiutils.end_of_directory()

    @staticmethod
    def disable_addon_source(addon_id):
        """ Disable the specified source. """
        source = AddonSource(addon_id=addon_id)
        source.disable()
        kodiutils.end_of_directory()

    @staticmethod
    def add_source():
        """ Add a new source. """
        source = ExternalSource(uuid=str(uuid4()),
                                name='External Source',  # Default name
                                enabled=False)
        source.save()

        # Go to edit page
        Menu.edit_source(source.uuid)

    @staticmethod
    def delete_source(uuid):
        """ Add a new source. """
        sources = ExternalSource.detect_sources()
        source = next(source for source in sources if source.uuid == uuid)
        source.delete()

        kodiutils.end_of_directory()

    @staticmethod
    def edit_source(uuid, edit=None):
        """ Edit a custom source. """
        sources = ExternalSource.detect_sources()
        source = next(source for source in sources if source.uuid == uuid)

        if source is None:
            kodiutils.container_refresh(kodiutils.url_for('show_sources'))
            return

        if edit == 'name':
            name = kodiutils.input_dialog(heading='Enter name', message=source.name)
            if name:
                source.name = name
                source.save()

        elif edit == 'enabled':
            source.enabled = not source.enabled
            source.save()

        elif edit == 'playlist':
            new_type, new_source = Menu._select_source(source.playlist_type, source.playlist_uri, '.m3u|.m3u8')
            if new_type is not None:
                source.playlist_type = new_type
                source.playlist_uri = new_source
                source.save()

        elif edit == 'guide':
            new_type, new_source = Menu._select_source(source.epg_type, source.epg_uri, mask='.xml|.xmltv')
            if new_type is not None:
                source.epg_type = new_type
                source.epg_uri = new_source
                source.save()

        listing = [
            TitleItem(
                title='[B]%s:[/B] %s' % (kodiutils.localize(30020), source.name),
                path=kodiutils.url_for('edit_source', uuid=source.uuid, edit='name'),
                info_dict=dict(
                    plot=kodiutils.localize(30021),
                ),
                art_dict=dict(
                    icon='empty.png',
                ),
            ),
            TitleItem(
                title='[B]%s:[/B] %s' % (kodiutils.localize(30022),  # Enabled
                                         kodiutils.localize(30024) if source.enabled else kodiutils.localize(30025)),  # Yes, No
                path=kodiutils.url_for('edit_source', uuid=source.uuid, edit='enabled'),
                info_dict=dict(
                    plot=kodiutils.localize(30023),
                ),
                art_dict=dict(
                    icon='icons/infodialogs/enabled.png' if source.enabled else 'icons/infodialogs/disable.png',
                    poster='empty.png',
                ),
            ),
            TitleItem(
                title='[B]%s:[/B] %s' % (kodiutils.localize(30026), source.playlist_uri),
                path=kodiutils.url_for('edit_source', uuid=source.uuid, edit='playlist'),
                info_dict=dict(
                    plot=kodiutils.localize(30027),
                ),
                art_dict=dict(
                    icon='empty.png',
                ),
            ),
            TitleItem(
                title='[B]%s:[/B] %s' % (kodiutils.localize(30028), source.epg_uri),
                path=kodiutils.url_for('edit_source', uuid=source.uuid, edit='guide'),
                info_dict=dict(
                    plot=kodiutils.localize(30029),
                ),
                art_dict=dict(
                    icon='empty.png',
                ),
            )
        ]

        kodiutils.show_listing(listing, category=30010, sort=['unsorted'], update_listing=edit is not None)

    @staticmethod
    def _select_source(current_type, current_source, mask):
        """ Select a source """
        new_source = current_source
        new_type = current_type

        res = kodiutils.show_context_menu([kodiutils.localize(30032),  # None
                                           kodiutils.localize(30030),  # Enter URL
                                           kodiutils.localize(30031)])  # Browse for file
        if res == -1:
            # User has cancelled
            return None, None

        if res == 0:
            # None
            new_source = None
            new_type = ExternalSource.TYPE_NONE

        elif res == 1:
            # Enter URL
            url = kodiutils.input_dialog(heading=kodiutils.localize(30030),  # Enter URL
                                         message=current_source if current_type == ExternalSource.TYPE_URL else '')
            if url:
                new_source = url
                new_type = ExternalSource.TYPE_URL

        elif res == 2:
            # Browse for file...
            filename = kodiutils.file_dialog(kodiutils.localize(30031), mask=mask,  # Browse for file
                                             default=current_source if current_type == ExternalSource.TYPE_FILE else '')
            if filename:
                # Simple loop prevention
                if filename in [os.path.join(kodiutils.addon_profile(), IPTV_SIMPLE_PLAYLIST),
                                os.path.join(kodiutils.addon_profile(), IPTV_SIMPLE_EPG)]:
                    return None, None

                new_source = filename
                new_type = ExternalSource.TYPE_FILE

        return new_type, new_source
