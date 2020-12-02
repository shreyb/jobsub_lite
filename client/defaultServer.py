from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from future import standard_library
standard_library.install_aliases()
import constants
import random


def defaultServer():
    defsrv = getattr(constants, 'JOBSUB_SERVER', None)
    if defsrv is not None:
        return defsrv
    else:
        deflist = getattr(constants, 'JOBSUB_SERVER_LIST', None)
        if deflist is not None:
            ln = len(deflist) - 1
            return deflist[random.randint(0, ln)]
        else:
            raise Exception("no default server set in constants.py")



if __name__ == '__main__':
    # tested with python2.7 and python3.6
    srv = defaultServer()
    assert(srv)
    print('test: OK')

