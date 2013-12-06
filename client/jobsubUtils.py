#!/usr/bin/env python

import platform
import os

def is_os_macosx():
    return platform.system() == 'Darwin'

def is_os_linux():
    return platform.system() == 'Linux'


def which(program):
    """
    Implementation of which command in python.

    @return: Path to the binary
    @rtype: string
    """

    def is_exe(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None
