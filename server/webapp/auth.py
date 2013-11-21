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


def check_auth(subject_dn, accountinggroup):
    result = execute_gums_command(subject_dn, accountinggroup)
    if result['out'][0].startswith('null') or len(result['err']) > 0:
        return False
    else:
        return True

