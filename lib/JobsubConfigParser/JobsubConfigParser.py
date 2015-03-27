from ConfigParser import SafeConfigParser
import os
import socket
try:
    import logger
except ImportError:
    import fakelogger as logger

class JobsubConfigParser(object):

    def __init__(self,group=None,submit_host=None):
        self.cnf=self.findConfigFile()
        self.parser=SafeConfigParser()
        self.group=group
        if self.group is None:
            self.group=os.environ.get("GROUP",None)
        self.submit_host=submit_host
        if self.submit_host is None:
            self.submit_host=os.environ.get("SUBMIT_HOST",None)
        if self.submit_host is None:
            self.submit_host=socket.gethostname()
        self.parser.read(self.cnf)

    def get_submit_host(self):
        return self.submit_host

    def sections(self):
        return self.parser.sections()
        
    def iniFile(self):
        return self.cnf
        
    def options(self,sect):
        os = []
        od = []
        if sect == self.submit_host and \
                self.group is not None:
            od = self.options(self.group)
        else:
            if self.has_section('default'):
                od=self.parser.options('default')
        if self.has_section(sect):
            os=self.parser.options(sect)
        for opt in od:
            if opt not in os:
                os.append(opt)
        return os

    def has_section(self,sect):
        return self.parser.has_section(sect)

    def has_option(self,sect,opt):
       all_opts=self.options(sect)
       return opt in all_opts 

    def items(self,sect):
        pairs=[]
        logger.log(sect)
        if self.parser.has_section('default'):
            pairs.extend(self.parser.items('default'))
        if sect==self.submit_host and self.parser.has_section(self.group):
            pairs.extend(self.parser.items(self.group))
        if self.parser.has_section(sect):
            pairs.extend(self.parser.items(sect))
        valdict=dict(pairs)
        return valdict.items()

    def get(self,sect,opt):
        itm=self.items(sect)
        valdict=dict(itm)
        if valdict.has_key(opt):
            val=valdict[opt]
            return val.strip("'")
        return None
                        
                

    def supportedGroups(self,host=None):
        if host is None:
            host=self.submit_host
        if host is None:
            host=socket.gethostname()
        str=self.get(host,'supported_groups')
        if str is not None:
            return str.split()
        return []


    def findConfigFile(self):
        #logger.log("findConfigFile")
        cnf = os.environ.get("JOBSUB_INI_FILE",None)
        ups=os.environ.get("JOBSUB_TOOLS_DIR",'')+"/bin/jobsub.ini"
        ups_ini_file = cnf==ups
        if cnf is not None: 
            return cnf
        for x in [ "PWD", "HOME" ]:
            path=os.environ.get(x)
            if path is None:
                path='/dev/null'
            cnf=path + "/jobsub.ini"
            ups_ini_file = cnf==ups
            if os.path.exists(cnf):
                if not ups_ini_file:
                    logger.log("using %s for jobsub config"%cnf)
                return cnf
        if os.path.exists(ups):
            #logger.log("using %s for jobsub config"%ups)
            return ups
        else:
            logger.log("error no config file found!")
        return None

        
