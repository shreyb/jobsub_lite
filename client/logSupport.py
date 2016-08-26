#!/usr/bin/env python

import logging
import sys

DEBUG_MODE = False

# Function to do nothing
dprint = lambda *a: None


def init_logging(debug_mode):
    global dprint
    if debug_mode:
        DEBUG_MODE = True

        def dprint(*args):
            for arg in args:
                print arg,
            print
