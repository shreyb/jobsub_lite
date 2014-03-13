#!/usr/bin/env python

from ConfigParser import SafeConfigParser
from JobsubConfigParser import *
import commands, os, sys, string, tempfile




def runConfig():
    fn = tempfile.mktemp(suffix='.sh')
    fd = open(fn,"w")
    vars = os.environ.get("JOBSUB_INI_VARS")
    for var in vars.split():
        fd.write("unset %s\n",var)
    fd.close()
    print fn

if __name__ == '__main__':
    runConfig()
