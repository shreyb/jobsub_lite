#!/usr/bin/env python
# $Id$
from JobSettings import JobSettings
import os
from optparse import OptionGroup


class NovaSettings(JobSettings):

    def __init__(self):
        super(NovaSettings, self).__init__()
        self.settings['nova_condor'] = os.environ.get(
            "GROUP_CONDOR", "/this/is/bogus")

        self.settings[
            'defaultrelarea'] = "/grid/fermiapp/nova/software_releases"
        self.settings['rp'] = ""

    def initCmdParser(self):
        cmdParser = self.cmdParser
        # print "NovaSettings.initCmdParser()"
        self.nova_group = OptionGroup(self.cmdParser, "Nova Specific Options")
        self.cmdParser.add_option_group(self.nova_group)
        self.nova_group.add_option("-i", dest="reldir",
                                   action="store", type="string",
                                   help="release_directory for Nova Software ")
        self.nova_group.add_option("-t", dest="testreldir",
                                   action="store", type="string",
                                   help="release_directory for test Nova Software ")
        self.nova_group.add_option("-r", dest="rel",
                                   action="store", type="string",
                                   help="release_version for  Nova Software ")
        return super(NovaSettings, self).initCmdParser()

    def makeWrapFilePostamble(self):
        # print "nova.makeWrapFilePostamble"
        settings = self.settings
        return super(NovaSettings, self).makeWrapFilePostamble()

    def makeWrapFilePreamble(self):
        relfmt = """
  export NOVA_SETUP_DIR=/grid/fermiapp/nova/novaart/novasoft/setup/
  unset SETUP_UPS SETUPS_DIR
  . /grid/fermiapp/nova/products/db/.upsfiles/configure/v4_7_4a_Linux+2_/setups.sh

  setup_nova()
         {
           . $NOVA_SETUP_DIR/setup_novasoft_nusoft.sh $*
         }
  setup_nova -r  %s %s """

        relfmt2 = """
    echo "Running 'srt_setup -a' in  %s"
    here=`/bin/pwd`
    cd %s
    srt_setup -a
    cd $here """

        relfmt3 = """source /grid/fermiapp/nova/novaart/novasvn/srt/srt.sh
export EXTERNALS=/nusoft/app/externals
source $SRT_DIST/setup/setup_novasoft.sh -r %s"""

        # print "novasettings makeFilePreamble"
        super(NovaSettings, self).makeWrapFilePreamble()
        settings = self.settings
        # print settings['wrapfile']

        f = open(settings['wrapfile'], 'a')

        f.write("#NovaSettingsPreamble\n")

        if ('rel' in settings):
            f.write(relfmt3 % (settings['rel']))
        if ('testreldir' in settings):
            f.write("#NovaSettingsPreamble2\n")

            f.write(relfmt2 % (settings['testreldir'], settings['testreldir']))

        f.write("\n")
        f.close()
