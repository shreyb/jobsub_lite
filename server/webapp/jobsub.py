import logger
import os
import socket


from JobsubConfigParser import JobsubConfigParser


def is_supported_accountinggroup(accountinggroup):
    rc = False
    try:
        p = JobsubConfigParser()
        groups = p.supportedGroups()
        rc = (accountinggroup in groups)
    except:
        logger.log('Failed to get accounting groups: ', traceback=True)

    return rc


def get_supported_accountinggroups():
    rc = list()
    try:
        p = JobsubConfigParser()
        rc = p.supportedGroups()
    except:
        logger.log('Failed to get accounting groups: ', traceback=True)

    return rc

def get_command_path_root():
       p = JobsubConfigParser()
       submit_host=os.environ.get('SUBMIT_HOST',socket.gethostname())
       #logger.log('searching for section %s'%submit_host, traceback=True)
       if p.has_section(submit_host):
               if p.has_option(submit_host,'command_path_root'):
                       val=p.get(submit_host,'command_path_root')
                       #logger.log('returning %s for command_path_root'%val)
                       return val
       return '/opt/jobsub/uploads'

