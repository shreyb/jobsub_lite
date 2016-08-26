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
