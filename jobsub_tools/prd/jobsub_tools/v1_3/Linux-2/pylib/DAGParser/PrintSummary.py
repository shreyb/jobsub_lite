#!/usr/bin/env python
import sys 

from DAGManParser import DAGManLogParser

d=DAGManLogParser(sys.argv[1],0,0)
d.write(1)
