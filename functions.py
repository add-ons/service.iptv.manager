# -*- coding: utf-8 -*-
""" Functions entry point """
from __future__ import absolute_import, division, unicode_literals

import sys

from resources.lib import functions

functions.run(sys.argv[1], sys.argv[:1])
