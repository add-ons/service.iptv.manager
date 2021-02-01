# -*- coding: utf-8 -*-
""" Addon code """

from __future__ import absolute_import, division, unicode_literals

import logging

import routing

from resources.lib import kodilogging

routing = routing.Plugin()  # pylint: disable=invalid-name

_LOGGER = logging.getLogger(__name__)


@routing.route('/')
def show_main_menu():
    """ Show the main menu """
    from resources.lib.modules.menu import Menu
    Menu().show_mainmenu()


@routing.route('/settings')
def show_settings():
    """ Show the sources menu """
    from resources.lib.modules.menu import Menu
    Menu().show_settings()


@routing.route('/sources')
def show_sources():
    """ Show the sources menu """
    from resources.lib.modules.menu import Menu
    Menu().show_sources()


@routing.route('/sources/add')
def add_source():
    """ Add a source """
    from resources.lib.modules.menu import Menu
    Menu().add_source()


@routing.route('/sources/edit/<uuid>')
@routing.route('/sources/edit/<uuid>/<edit>')
def edit_source(uuid, edit=None):
    """ Edit a source """
    from resources.lib.modules.menu import Menu
    Menu().edit_source(uuid, edit)


@routing.route('/sources/delete/<uuid>')
def delete_source(uuid):
    """ Delete a source """
    from resources.lib.modules.menu import Menu
    Menu().delete_source(uuid)


@routing.route('/sources/refresh')
def refresh():
    """ Show the sources menu """
    from resources.lib.modules.menu import Menu
    Menu().refresh()


@routing.route('/sources/enable/<addon_id>')
def enable_source(addon_id):
    """ Show the sources menu """
    from resources.lib.modules.menu import Menu
    Menu().enable_addon_source(addon_id)


@routing.route('/sources/disable/<addon_id>')
def disable_source(addon_id):
    """ Show the sources menu """
    from resources.lib.modules.menu import Menu
    Menu().disable_addon_source(addon_id)


@routing.route('/install')
def install():
    """ Setup IPTV Simple """
    from resources.lib.modules.menu import Menu
    Menu().show_install()


@routing.route('/play')
def play():
    """ Play from Context Menu (used in Kodi 18) """
    from resources.lib.modules.contextmenu import ContextMenu
    ContextMenu().play()


def run(params):
    """ Run the routing plugin """
    kodilogging.config()
    routing.run(params)
