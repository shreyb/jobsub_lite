import cherrypy
import logger

from subprocess import Popen, PIPE


def execute_gums_command(subject_dn, accountinggroup):
    command = '/usr/bin/gums-host|mapUser|-g|https://gums.fnal.gov:8443/gums/services/GUMSXACMLAuthorizationServicePort|%s|-f|/fermilab/%s' % (subject_dn, accountinggroup)
    command = command.split('|')
    logger.log('gums command: %s' % command)
    pp = Popen(command, stdout=PIPE, stderr=PIPE)
    result = {
        'out': pp.stdout.readlines(),
        'err': pp.stderr.readlines()
    }
    logger.log('gums command result: %s' % str(result))
    return result


def _check_auth(subject_dn, accountinggroup):
    result = execute_gums_command(subject_dn, accountinggroup)
    if result['out'][0].startswith('null') or len(result['err']) > 0:
        return False
    else:
        return True


def check_auth(func):
    def check_auth_wrapper(self, acctgroup, *args, **kwargs):
        subject_dn = cherrypy.request.headers.get('Auth-User')
        if subject_dn is not None and acctgroup is not None:
            logger.log('subject_dn: %s, acctgroup: %s' % (subject_dn, acctgroup))
            if _check_auth(subject_dn, acctgroup):
                return func(self, acctgroup, *args, **kwargs)
            else:
                # return error for failed auth
                err = 'User authorization has failed'
                logger.log(err)
                rc = {'err': err}
        else:
            # return error for no subject_dn and acct group
            err = 'User has not supplied subject dn and/or accounting group'
            logger.log(err)
            rc = {'err': err}
    return check_auth_wrapper
