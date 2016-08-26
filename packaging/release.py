#!/usr/bin/env python

import sys
import os
import getopt
import optparse

sys.path.append(os.path.join(sys.path[0], '../lib'))
import ReleaseManagerLib


def usage():
    print "%s <version> <SourceDir> <ReleaseDir>" % os.path.basename(sys.argv[0])
    print ""
    print "Example: Release Candidate rc3 for v0.2 (ie version v0.2.rc3)"
    print "release.py --version=0.2 --rc=3 --source-dir=/cloud/login/parag/wspace/jobsub/code/jobsub --release-dir=/var/tmp/parag --rpm-release=1"
    print ""
    print "Example: Final Release v0.2"
    print "release.py --version=0.2 --source-dir=/cloud/login/parag/wspace/jobsub/code/jobsub --release-dir=/var/tmp/parag --rpm-release=1"
    print ""


def parse_opts(argv):
    # parser = optparse.OptionParser(usage='%prog [options]',
    parser = optparse.OptionParser(usage=usage(),
                                   version='v0.1',
                                   conflict_handler="resolve")
    parser.add_option('--version',
                      dest='version',
                      action='store',
                      metavar='<version>',
                      help='version to release')
    parser.add_option('--rc',
                      dest='rc',
                      default=None,
                      action='store',
                      metavar='<Release Candidate Number>',
                      help='Release Candidate')
    parser.add_option('--rpm-release',
                      dest='rpmRel',
                      default=1,
                      action='store',
                      metavar='<RPM Release Number>',
                      help='RPM Release Number')
    parser.add_option('--source-dir',
                      dest='srcDir',
                      action='store',
                      metavar='<source directory>',
                      help='directory containing the source code')
    parser.add_option('--release-dir',
                      dest='relDir',
                      action='store',
                      metavar='<release directory>',
                      help='directory to store release tarballs and webpages')

    if len(argv) < 5:
        print "ERROR: Insufficient arguments specified"
        parser.print_help()
        sys.exit(1)
    options, remainder = parser.parse_args(argv)
    if len(remainder) > 1:
        parser.print_help(file)
    if not required_args_present(options):
        print "ERROR: Missing required arguments"
        parser.print_help()
        sys.exit(1)
    return options


def required_args_present(options):
    try:
        if not (options.version and options.srcDir and options.relDir):
            return False
    except AttributeError:
        return False
    return True
#   check_required_args


# def main(ver, srcDir, relDir):
def main(argv):
    options = parse_opts(argv)
    # sys.exit(1)
    product = 'jobsub'
    ver = options.version
    rpm_rel = options.rpmRel
    rc = options.rc

    srcDir = options.srcDir
    relDir = options.relDir

    print "___________________________________________________________________"
    print "Creating following release"
    print "Product=%s Version=%s RC=%s RPMRelease=%s\nSourceDir=%s\nReleaseDir=%s" % (product, ver, rc, rpm_rel, srcDir, relDir)
    print "___________________________________________________________________"
    print
    rel = ReleaseManagerLib.Release(product, ver, rpm_rel, rc, srcDir, relDir)

    rel.addTask(ReleaseManagerLib.TaskClean(rel))
    rel.addTask(ReleaseManagerLib.TaskSetupReleaseDir(rel))
    rel.addTask(ReleaseManagerLib.TaskClientTar(rel))
    rel.addTask(ReleaseManagerLib.TaskServerRPM(rel))

    rel.executeTasks()
    rel.printReport()

if __name__ == "__main__":
    main(sys.argv)
