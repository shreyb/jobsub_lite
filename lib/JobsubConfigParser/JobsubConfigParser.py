from ConfigParser import SafeConfigParser
import os
import logger
import socket

class JobsubConfigParser(object):

	def __init__(self):
		self.cnf=self.findConfigFile()
		self.parser=SafeConfigParser()
		self.parser.read(self.cnf)

	def sections(self):
		return self.parser.sections()
	
	def options(self,sect):
		return self.parser.options(sect)

	def has_section(self,sect):
		return self.parser.has_section(sect)

	def items(self,sect):
		return self.parser.items(sect)

	def supportedGroups(self,host=None):
		if host is None:
			host=socket.gethostname()
		p=self.parser
		sect=p.sections()
		if host in sect:
			opt=p.options(host)
			if 'supported_groups' in opt:
				str=p.get(host,'supported_groups')
				return str.split()
		return None


        def findConfigFile(self):
                cnf = os.environ.get("JOBSUB_INI_FILE",None)
                if cnf is not None:
			#print "using %s for jobsub config"%cnf
			return cnf
		for x in [ "PWD", "HOME"]:
			cnf=os.environ.get(x)+"/jobsub.ini"
			if os.path.exists(cnf):
				logger.log("using %s for jobsub config"%cnf)
				return cnf
		logger.log("error no config file found!")
		return None

	
