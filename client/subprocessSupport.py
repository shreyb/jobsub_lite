#!/usr/bin/env python

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from encoding import force_text
from future import standard_library
standard_library.install_aliases()
import os
import subprocess
import six

#import shlex


class CalledProcessError(Exception):
    """This exception is raised when a process run by check_call() or
    check_output() returns a non-zero exit status.
    The exit status will be stored in the returncode attribute;
    check_output() will also store the output in the output attribute.
    """

    def __init__(self, returncode, cmd, output=None):
        self.returncode = returncode
        self.cmd = cmd
        self.output = output

    def __str__(self):
        return "Command '%s' returned non-zero exit status %s: %s" % (
            self.cmd, self.returncode, self.output)


def iexe_cmd(cmd, useShell=False, stdin_data=None, child_env=None):
    """
    Fork a process and execute cmd - rewritten to use select to avoid filling
    up stderr and stdout queues.

    The useShell value of True should be used sparingly.  It allows for
    executing commands that need access to shell features such as pipes,
    filename wildcards.  Refer to the python manual for more information on
    this.  When used, the 'cmd' string is not tokenized.

    One possible improvment would be to add a function to accept
    an array instead of a command string.

    @type cmd: string
    @param cmd: Sting containing the entire command including all arguments
    @type stdin_data: string
    @param stdin_data: Data that will be fed to the command via stdin
    @type env: dict
    @param env: Environment to be set before execution
    """
    stdoutdata = stderrdata = ""
    exitStatus = 0

    try:
        # Add in parent process environment, make sure that env ovrrides parent
        if child_env:
            for k in os.environ:
                if not k in child_env:
                    child_env[k] = os.environ[k]
        # otherwise just use the parent environment
        else:
            child_env = os.environ

        # Tokenize the commandline that should be executed.
        if useShell:
            command_list = ['%s' % cmd, ]
        else:
            #command_list = shlex.split(cmd.encode('utf8'))
            command_list = cmd.split()
        # launch process - Converted to using the subprocess module
        process = subprocess.Popen(command_list, shell=useShell,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   env=child_env)

        # GOTCHAS:
        # 1) stdin should be buffered in memory.
        # 2) Python docs suggest not to use communicate if the data size is
        #    large or unlimited. With large or unlimited stdout and stderr
        #    communicate at best starts trashing. So far testing for 1000000
        #    stdout/stderr lines are ok
        # 3) Do not use communicate when you are dealing with multiple threads
        #    or processes at same time. It will serialize the process voiding
        #    any benefits from multiple processes
        stdoutdata, stderrdata = process.communicate(input=stdin_data)
        exitStatus = process.returncode

    except OSError as e:
        err_str = "Error running '%s'\nStdout:%s\n"
        err_str += "Stderr:%s\nException OSError:%s"
        raise RuntimeError(err_str % (cmd, stdoutdata, stderrdata, e))
    return (force_text(stdoutdata), force_text(stderrdata))



if __name__ == '__main__':
    # tested with python2.7 and python3.6
    # quick test of a command that should work
    cmd = 'ls'
    out,err = iexe_cmd(cmd)
    assert(out != "")
    assert(err == "")
    #quick test of a command that should not work
    try:
        cmd = 'lssssssssss'
        out,err = iexe_cmd(cmd)
        assert(False)
    except RuntimeError as err:
        pass
    print("passed tests: OK")
