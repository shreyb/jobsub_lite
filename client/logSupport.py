#!/usr/bin/env python

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
import logging
import sys

DEBUG_MODE = False

# Function to do nothing
dprint = lambda *a: None


def init_logging(debug_mode):
    global dprint
    global DEBUG_MODE
    if debug_mode:
        DEBUG_MODE = True

        def dprint(*args):
            for arg in args:
                print(arg, end=' ')
            print()
