#!/usr/bin/env python

import os
import sys
import re
import traceback
import subprocessSupport


def fix_links(really_do_it=False):
    cmds = ["""condor_history -format "%s." clusterid -format "%s" procid -format " %s " owner  -format "%s\n" iwd """,
            """condor_q -format "%s." clusterid -format "%s" procid -format " %s " owner  -format "%s\n" iwd """]
    for cmd in cmds:
        cmd_out, cmd_err = subprocessSupport.iexe_cmd(cmd)
        if cmd_err:
            raise Exception("command %s returned %s" % (cmd, cmd_err))
        lines = cmd_out.split("\n")
        for line in lines:
            # print line
            parts = line.split()
            if len(parts) >= 3:
                (cluster, user, iwd) = line.split()
                base = os.path.dirname(iwd)
                newlink = "%s/%s" % (base, cluster)
                cmd2 = "ln -s %s %s" % (iwd, newlink)
                if not os.path.exists(newlink):
                    print "%s\n" % cmd2
                    if really_do_it:
                        ln_out, ln_err = subprocessSupport.iexe_cmd(cmd2)
                else:
                    print "#%s already exists, doing nothing\n" % newlink


def print_help():
    usage = """fix_sandbox_links, a program for fixing soft links
            for jobsub sandbox if they get messed up or for creating
            them for a server upgrade
            options:
            --test : print out the links that would be created
            but don't actually do it
            --fix-links: create the soft links that are needed
            for the sandbox downloader to work
"""

    print usage


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '--test':
            fix_links(False)
        elif sys.argv[1] == '--fix-links':
            fix_links(True)
        else:
            print_help()
    else:
        print_help()
