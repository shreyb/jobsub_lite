#!/usr/bin/env python

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
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

def splitall(path):
    """
    Split a path into its components, rather than just 
    into a filename and the rest of the path.
    
    Note that os.path.join(*splitall(path)) = path

    @return: List containing path components
    @rtype: list
    """
    path_parts = []
    while True:
        sp = os.path.split(path)
        if sp[0] == path:   # Absolute path root
            path_parts.insert(0, sp[0])
            break
        elif sp[1] == path:  # Relative path root
            path_parts.insert(0, sp[1])
            break
        else:
            path_parts.insert(0, sp[1])
            path = sp[0]
    return path_parts
