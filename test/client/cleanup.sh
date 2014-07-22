#!/bin/sh
find . -name '*out' -type f  -exec rm -f {} \;
find . -name '*log' -type f  -exec rm -f {} \;
/bin/rm -rf UNZIPDIR curl python 
/bin/rm -f  1 
