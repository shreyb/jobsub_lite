#!/usr/bin/env python

import os
import subprocess
import shutil
import string


class ExeError(RuntimeError):

    def __init__(self, str):
        RuntimeError.__init__(self, str)


class Release(object):

    def __init__(self, product, ver, rpm_rel, rc, srcDir, relDir='/tmp'):
        self.product = product
        self.version = ver
        self.rc = rc
        self.rpmRelease = rpm_rel

        self.clientVersion = self.version
        self.serverRPMVersion = self.version
        self.serverRPMRelease = self.rpmRelease

        if self.rc:
            self.clientVersion = '%s.rc%s' % (self.version, self.rc)
            self.serverRPMRelease = '0.%s.rc%s' % (self.rpmRelease, self.rc)

        self.versionString = self.clientVersion

        self.sourceDir = srcDir
        self.releaseDir = os.path.join(relDir, self.versionString)
        self.rpmbuildDir = os.path.join(self.releaseDir, 'rpmbuild')
        self.tasks = []

    def addTask(self, task):
        self.tasks.append(task)

    def executeTasks(self):
        for i in range(0, len(self.tasks)):
            task = self.tasks[i]
            print "************* Executing %s *************" % (self.tasks[i]).name
            task.execute()
            print "************* %s Status %s *************" % ((self.tasks[i]).name, (self.tasks[i]).status)

    def printReport(self):
        print 35 * "_"
        print "TASK" + 20 * " " + "STATUS"
        print 35 * "_"
        for i in range(0, len(self.tasks)):
            print "%-23s %s" % ((self.tasks[i]).name, (self.tasks[i]).status)
        print 35 * "_"


class TaskRelease(object):

    def __init__(self, name, rel):
        self.name = name
        self.release = rel
        self.status = 'INCOMPLETE'
    #   __init__

    def execute(self):
        raise ExeError(
            'Action execute not implemented for task %s' % self.name)
    #   execute


class TaskClean(TaskRelease):

    def __init__(self, rel):
        TaskRelease.__init__(self, 'Clean', rel)
    #   __init__

    def execute(self):
        cmd = 'rm -rf %s' % self.release.releaseDir
        execute_cmd(cmd)
        self.status = 'COMPLETE'
    #   execute


class TaskSetupReleaseDir(TaskRelease):

    def __init__(self, rel):
        TaskRelease.__init__(self, 'SetupReleaseDir', rel)
    #   __init__

    def execute(self):
        create_dir(self.release.releaseDir)
        create_dir(self.release.rpmbuildDir)
        self.status = 'COMPLETE'
    #   execute


class TaskTar(TaskRelease):

    def __init__(self, rel):
        TaskRelease.__init__(self, 'JobSubTar', rel)
        self.excludes = PackageExcludes()
        self.releaseFilename = 'glideinWMS_%s.tgz' % self.release.version
        self.excludePattern = self.excludes.commonPattern
        self.tarExe = which('tar')
        self.updateFileList = []
    #   __init__

    def execute(self):
        exclude = ""
        if len(self.excludePattern) > 0:
            exclude = "--exclude='" + \
                string.join(self.excludePattern, "' --exclude='") + "'"
        src_dir = '%s/../src/%s' % (self.release.releaseDir,
                                    self.release.version)
        cmd = 'rm -rf %s; mkdir -p %s; cp -r %s %s/%s' % \
              (src_dir, src_dir, self.release.sourceDir, src_dir, self.releaseDirname)
        print "%s" % cmd
        execute_cmd(cmd)
        for f in self.updateFileList:
            self.updateFile(f)
        cmd = 'cd %s; %s %s -czf %s/%s %s' % \
              (src_dir, self.tarExe, exclude, self.release.releaseDir,
               self.releaseFilename, self.releaseDirname)
        print "%s" % cmd
        execute_cmd(cmd)
        self.status = 'COMPLETE'

    def updateFile(self, fileName):
        print 'updating %s' % fileName
        fd = open(fileName, 'r')
        specs = fd.readlines()
        fd.close()

        fd = open(fileName, 'w')
        for line in specs:
            line = line.replace('__VERSION__', self.release.serverRPMVersion)
            line = line.replace('__RELEASE__', self.release.serverRPMRelease)
            fd.write(line)
        fd.close()


class TaskClientTar(TaskTar):

    def __init__(self, rel):
        TaskTar.__init__(self, rel)
        self.name = 'JobSubClientTar'
        self.releaseDirname = 'jobsub'
        self.releaseFilename = 'jobsub-client-v%s.tgz' % self.release.clientVersion
        self.excludePattern = self.excludes.clientPattern
        _constants_py = os.path.join(self.release.releaseDir, '..', 'src',
                                     self.release.serverRPMVersion, 'jobsub', 'client', 'constants.py')
        self.updateFileList.append(_constants_py)


class TaskServerRPM(TaskTar):

    def __init__(self, rel):
        TaskTar.__init__(self, rel)
        self.name = 'JobSubServerRPM'
        self.releaseDirname = 'jobsub-%s' % self.release.serverRPMVersion
        self.releaseFilename = 'jobsub-%s.tar.gz' % self.release.serverRPMVersion
        self.excludePattern = self.excludes.serverPattern

        edit_dir = os.path.join(self.release.releaseDir,
                                '..', 'src', self.release.serverRPMVersion)
        _rpm_specs_infile = "%s/jobsub-%s/packaging/jobsub_server.spec" % (
            edit_dir, self.release.serverRPMVersion)
        _jobsub_api_py_infile = "%s/jobsub-%s/server/webapp/jobsub_api.py" % (
            edit_dir, self.release.serverRPMVersion)
        self.updateFileList.append(_rpm_specs_infile)
        self.updateFileList.append(_jobsub_api_py_infile)
    #   __init__

    def execute(self):
        # First build the source tarball
        TaskTar.execute(self)

        rpm_dirs = ['BUILD', 'RPMS', 'SOURCES', 'SPECS', 'SRPMS']
        rpm_src_dir = os.path.join(self.release.rpmbuildDir, 'SOURCES')
        rpm_specs_dir = os.path.join(self.release.rpmbuildDir, 'SPECS')
        rpm_file = os.path.join(self.release.rpmbuildDir, 'RPMS', 'noarch',
                                'jobsub-%s-%s.noarch.rpm' % (self.release.serverRPMVersion, self.release.serverRPMRelease))
        rpm_specs_infile = os.path.join(
            self.release.sourceDir, 'packaging', 'jobsub_server.spec')
        rpm_specs_outfile = os.path.join(rpm_specs_dir, 'jobsub_server.spec')

        # Create directories required by rpmbuild
        for dir in rpm_dirs:
            create_dir(os.path.join(self.release.rpmbuildDir, dir))

        # Move the source tarball in place
        shutil.move(os.path.join(self.release.releaseDir, self.releaseFilename),
                    rpm_src_dir)

        # Create rpmmacros file
        rpm_macros_file = os.path.join(os.path.expanduser('~'), '.rpmmacros')
        fd = open(rpm_macros_file, 'w')
        fd.write('%%_topdir %s\n' % self.release.rpmbuildDir)
        fd.write('%%_tmppath %s\n' % '/tmp')
        fd.close()

        # Create the rpm
        cmd = 'rpmbuild -bb %s' % self.updateFileList[0]
        print "%s" % cmd
        execute_cmd(cmd)
        rpm_filename = os.path.basename(rpm_file)
        shutil.copyfile(rpm_file, os.path.join(
            self.release.releaseDir, rpm_filename))


class PackageExcludes(object):

    def __init__(self):

        self.commonPattern = [
            'CVS',
            '.git*',
            '.DS_Store',
        ]

        # Patterns that need to be excluded from the client tarball
        self.clientPattern = [
            'CVS',
            '.git*',
            '.DS_Store',
            'client/*.pyc',
            'config',
            'jobsub_tools',
            'lib',
            'packaging',
            'server',
            'test',
            'ups_jobsub_client',
            'config_files',
            'pylint.sh',
            'pydoc.sh',
        ]

        # Patterns that need to be excluded from the server tarball
        self.serverPattern = [
            'CVS',
            '.git*',
            '.t*',
            '.DS_Store',
            'client',
            'config',
            'jobsub_tools',
            'packaging',
            'test',
            'ups_jobsub_client',
            '*.pyc',
            '*.pyo',
            'doc',
            '*.log',
            '*.sock',
            'setup',
            'Readme',
            'dev_use_virtual_env.sh',
            'requirements.txt',
            'config_files',
            'pylint.sh',
            'pydoc.sh',
        ]
############################################################
#
# P R I V A T E, do not use
#
############################################################


def create_dir(dir, mode=0o755, errorIfExists=False):
    try:
        os.makedirs(dir, mode=0o755)
    except OSError as xxx_todo_changeme:
        (errno, stderror) = xxx_todo_changeme.args
        if (errno == 17) and (errorIfExists == False):
            print 'Dir already exists reusing %s' % dir
        else:
            raise
    except Exception:
        raise

# can throw ExeError


def execute_cmd(cmd, stdin_data=None):
    child = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if stdin_data is not None:
        child.stdin.write(stdin_data)

    tempOut = child.stdout.readlines()
    tempErr = child.stderr.readlines()
    child.communicate()
    # child.childerr.close()
    try:
        errcode = child.wait()
    except OSError as e:
        if len(tempOut) != 0:
            # if there was some output, it is probably just a problem of timing
            # have seen a lot of those when running very short processes
            errcode = 0
        else:
            raise ExeError("Error running '%s'\nStdout:%s\nStderr:%s\nException OSError: %s" % (
                cmd, tempOut, tempErr, e))
    if (errcode != 0):
        raise ExeError("Error running '%s'\ncode %i:%s" % (
            cmd, errcode, tempErr))
    return tempOut


"""
def execute_cmd1(cmd, stdin_data=None):
    #child = subprocess.Popen(shlex.split(cmd), stdin=stdin_data)
    child=popen2.Popen3(cmd,True)
    if stdin_data!=None:
        child.tochild.write(stdin_data)
    child.tochild.close()
    tempOut = child.fromchild.readlines()
    child.fromchild.close()
    tempErr = child.childerr.readlines()
    child.childerr.close()
    try:
        errcode = child.wait()
    except OSError, e:
        if len(tempOut) != 0:
            # if there was some output, it is probably just a problem of timing
            # have seen a lot of those when running very short processes
            errcode = 0
        else:
            raise ExeError, "Error running '%s'\nStdout:%s\nStderr:%s\nException OSError: %s"%(cmd,tempOut,tempErr,e)
    if (errcode != 0):
        raise ExeError, "Error running '%s'\ncode %i:%s"%(cmd,errcode,tempErr)
    return tempOut
"""


def which(program):
    """
    Implementation of which command in python.

    @return: Path to the binary
    @rtype: string
    """

    def is_exe(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None
