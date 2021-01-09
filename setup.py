#!/usr/bin/python
# -*- coding: utf-8 -*-

import os.path
from xml.dom.minidom import parse
from setuptools import setup

project_dir = os.path.dirname(os.path.abspath(__file__))
metadata = parse(os.path.join(project_dir, 'addon.xml'))
addon_version = metadata.firstChild.getAttribute('version')

setup(
    name='iptvmanager',
    version=addon_version,
    url='https://github.com/add-ons/service.iptv.manager',
    author='Michaël Arnauts',
    description='An IPTV Manager module',
    long_description=open(os.path.join(project_dir, 'README.md')).read(),
    keywords='Kodi, plugin',
    license='GPL-3.0',
    package_dir={'': 'resources'},
    py_modules=['iptvmanager'],
    zip_safe=False,
)