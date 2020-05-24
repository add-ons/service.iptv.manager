# -*- coding: utf-8 -*-
"""This is the actual IPTV Manager script entry point"""

from __future__ import absolute_import, division, unicode_literals
import sys
from resources.lib.functions import run

if len(sys.argv) > 1:
    run(sys.argv)
else:
    run([-1, 'open_settings'])
