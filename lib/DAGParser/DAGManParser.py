#########################################
#
# DAGMan file parsers
#
# Written by: I. Sfiligoi
#
#########################################

import string
import time
import os
import stat
import xml_format
import re
import socket

status_strings = {0: "Wait", 1: "Idle", 2: "Running", 3: "Removed",
                  4: "Completed", 5: "Held", 6: "Suspended", 7: "Assigned"}
# add also inverse hash
status_codes = {}
for i in status_strings.keys():
    status_codes[status_strings[i]] = i


# Two attributes:
# jids - dictionary of Condor JobIDs
#        each id contains a dictionary with:
#         section     - section name (e.g "Section_43") (only if not ignore_sections)
#         current     - status of the job (any status_code)
#         nr_starts   - number of starts
#         nr_suspends - number of suspends
#         nr_holds    - number of holds
#         lost_secs   - number of seconds lost due to evict and/or abort events
#        optionals: (date and time are present iff not utime_only
#         submit - {date,time,utime}
#         exe    - {date,time,utime,node,port}
#         end    - {date,time,utime,status,retcode,user,sys}
#                  where status can be "Success" or "Failed"
#                        retcode avail only if status=="Success"
#         abort  - {date,time,utime}
#         hold   - {date,time,utime}
#         release- {date,time,utime}
#         suspend- {date,time,utime}
# sections - dictionary of (section_name,jid)
class DAGManLogParser:

    def parseSubmit(self, jid, datetime, other, block, ignore_sections):
        if not ignore_sections:
            # extract section
            # example line:
            #    DAG Node: Section_66
            datalist = string.split(block[0])
            if len(datalist) < 3:
                raise Exception("Invalid submit data: %s" % block[0])
            if (datalist[0] != 'DAG') and (datalist[1] != 'Node:'):
                raise Exception("Invalid submit data: %s" % block[0])
            section = datalist[2]

            self.jids[jid] = {"section": section, "submit": datetime, "current": status_codes[
                "Idle"], "nr_starts": 0, "lost_secs": 0, "nr_suspends": 0, "nr_holds": 0}
            self.sections[section] = jid
        else:
            self.jids[jid] = {"submit": datetime, "current": status_codes[
                "Idle"], "nr_starts": 0, "lost_secs": 0, "nr_suspends": 0, "nr_holds": 0}

    def parseExecute(self, jid, datetime, other, block):
        self.jids[jid]["nr_starts"] = self.jids[jid]["nr_starts"] + 1
        # extract node
        # example line:
        # Job executing on host: <131.225.240.52:33076>
        try:
            exeurl = string.split(other)[4]
            exeurllist = string.split(exeurl, ":")
            exehost = exeurllist[0][1:]
            #exeport = int(exeurllist[1][:-1])
            m = re.match("(\d+)", exeurllist[1])
            exeport = m.group(1)
        except:
            # Protect just in case
            exehost = "unknown"
            exeport = -1
        datetime["node"] = exehost
        datetime["port"] = exeport

        # if restarting, remove evict, hold and release history
        if "evict" in self.jids[jid]:
            del self.jids[jid]["evict"]
        if "hold" in self.jids[jid]:
            del self.jids[jid]["hold"]
        if "release" in self.jids[jid]:
            del self.jids[jid]["release"]
        if "suspend" in self.jids[jid]:
            del self.jids[jid]["suspend"]

        self.jids[jid]["exe"] = datetime
        self.jids[jid]["current"] = status_codes["Running"]

    def parseDone(self, jid, datetime, other, block):
        if self.jids[jid]["current"] != status_codes["Running"]:
            # never really run, assume fake event for removing
            self.jids[jid]["abort"] = datetime
            self.jids[jid]["current"] = status_codes["Removed"]
            return

        # find out how it finished
        statuslist = string.split(block[0])
        if statuslist[0] == "(1)":
            status = "Success"
            datetime["retcode"] = int(statuslist[5][:-1])
        else:
            status = "Failed"
        datetime["status"] = status

        for i in range(1, len(block)):
            linelist = string.split(block[i])
            if linelist[0] == "Usr":
                days = int(linelist[1])
                time = string.split(linelist[2], ":")
                hours = int(time[0])
                mins = int(time[1])
                secs = int(time[2][:-1])  # ss,
                usrsecs = ((days * 24 + hours) * 60 + mins) * 60 + secs
                datetime["user"] = usrsecs

                days = int(linelist[4])
                time = string.split(linelist[5], ":")
                hours = int(time[0])
                mins = int(time[1])
                secs = int(time[2])
                syssecs = ((days * 24 + hours) * 60 + mins) * 60 + secs
                datetime["sys"] = syssecs
                break  # we are interested only in the first time line

        self.jids[jid]["end"] = datetime
        self.jids[jid]["current"] = status_codes["Completed"]

    def parseAbort(self, jid, datetime, other, block):
        self.jids[jid]["abort"] = datetime
        if self.jids[jid]["current"] == status_codes["Running"]:
            self.jids[jid]["lost_secs"] = self.jids[jid]["lost_secs"] + \
                (datetime["utime"] - self.jids[jid]["exe"]["utime"])
        self.jids[jid]["current"] = status_codes["Removed"]

    def parseEvict(self, jid, datetime, other):
        self.jids[jid]["evict"] = datetime
        if self.jids[jid]["current"] == status_codes["Running"]:
            self.jids[jid]["lost_secs"] = self.jids[jid]["lost_secs"] + \
                (datetime["utime"] - self.jids[jid]["exe"]["utime"])
        self.jids[jid]["current"] = status_codes["Idle"]

    def parseHold(self, jid, datetime, other, block):
        if "release" in self.jids[jid]:
            del self.jids[jid]["release"]
        self.jids[jid]["nr_holds"] = self.jids[jid]["nr_holds"] + 1
        self.jids[jid]["hold"] = datetime
        self.jids[jid]["current"] = status_codes["Held"]

    def parseRelease(self, jid, datetime, other, block):
        self.jids[jid]["release"] = datetime
        self.jids[jid]["current"] = status_codes["Idle"]

    def parseSuspend(self, jid, datetime, other, block):
        self.jids[jid]["suspend"] = datetime
        self.jids[jid]["nr_suspends"] = self.jids[jid]["nr_suspends"] + 1
        self.jids[jid]["current"] = status_codes["Suspended"]

    def parseUnsuspend(self, jid, datetime, other, block):
        if "suspend" in self.jids[jid]:
            del self.jids[jid]["suspend"]
        self.jids[jid]["current"] = status_codes["Running"]

    def mktime(self, datestr, timestr):
        datelist = string.split(datestr, "/")
        timelist = string.split(timestr, ":")
        month = int(datelist[0])
        day = int(datelist[1])
        hour = int(timelist[0])
        min = int(timelist[1])
        sec = int(timelist[2])

        year = self.curtimelist[0]  # try current year
        utime = time.mktime((year, month, day, hour, min, sec, -1, -1, -1))
        if (utime > (self.curtime + 360000)
            ):  # probably the date was in the past year
            utime = time.mktime(
                (year - 1, month, day, hour, min, sec, -1, -1, -1))
        return utime

    def parseBlock(self, block, ignore_sections, utime_only):
        optype, jidstr, date, time, other = string.split(block[0], " ", 4)
        jid = int(string.split(jidstr, '.', 1)[0][1:])

        if utime_only:
            datetime = {"utime": self.mktime(date, time)}
        else:
            datetime = {"date": date, "time": time,
                        "utime": self.mktime(date, time)}

        if optype == "000":
            self.parseSubmit(jid, datetime, other, block[1:], ignore_sections)
        else:
            if jid not in self.jids:
                # protect against errors in the logfile
                self.parseSubmit(jid, datetime, None, None, 1)

            if optype == "001":
                self.parseExecute(jid, datetime, other, block[1:])
            elif optype == "009":
                self.parseAbort(jid, datetime, other, block[1:])
            elif (optype == "004") or (optype == "024"):
                self.parseEvict(jid, datetime, other)
            elif optype == "007":
                self.parseEvict(jid, datetime, other)
            elif optype == "005":
                self.parseDone(jid, datetime, other, block[1:])
            elif optype == "010":
                self.parseSuspend(jid, datetime, other, block[1:])
            elif optype == "011":
                self.parseUnsuspend(jid, datetime, other, block[1:])
            elif optype == "012":
                self.parseHold(jid, datetime, other, block[1:])
            elif optype == "013":
                self.parseRelease(jid, datetime, other, block[1:])
            else:
                pass  # everything else can be safely ignored

    def parseFile(self, fd, ignore_sections, utime_only):
        changed = 0

        i = 0
        block_nr = 0
        while True:
            # split the text file in blocks
            j = i
            lines = [fd.readline()]
            while (len(lines[-1]) > 0) and (lines[-1] != "...\n"):
                j = j + 1
                lines.append(fd.readline())

            if len(lines[-1]) == 0:
                # found EOF, this block is not complete
                return changed

            del lines[-1]  # last list is "...", so not interesting
            try:
                # print "calling
                # parseBlock(lines=%s,ignore_sections=%s,utime_only=%s)"%(lines,ignore_sections,utime_only)
                self.parseBlock(lines, ignore_sections, utime_only)
            except TypeError as msg:
                raise Exception("Lines %i-%i Block %i: %s" % (
                    i, j, block_nr, msg))
            fd.release()
            changed = 1

            # iterate
            i = j + 1
            block_nr = block_nr + 1

    def get_new_events(self, jid, prev_time):
        new_events = {}
        for k in jid.keys():
            el = jid[k]
            if isinstance(el, type({})):
                if 'utime' in el:
                    utime = el['utime']
                    if utime > prev_time:
                        new_events[k] = utime
        return new_events

    # main
    #****************************************
    def __init__(self, logfilename, ignore_sections=0,
                 utime_only=1, use_cache=0, cache_dir=None):
        if use_cache:
            if cache_dir is None:
                cache_basename = logfilename
            else:
                cache_basename = cache_dir + "/cache_" + \
                    string.replace(logfilename, "/", "_")
            #lio = DiskModule.CachedLineIO(logfilename,cache_basename+(".%i%i"%(ignore_sections,utime_only))+'.dmpi',[{},{}])
        else:
            lio = LineIO(logfilename, [{}, {}])
        # the log files can be big, so use LineIO class
        lio.open()
        try:
            self.jids, self.sections = lio.fields

            # will be needed to convert times, since we don't have the year in
            # the log files
            self.curtime = os.stat(logfilename)[stat.ST_MTIME]
            self.curtimelist = time.localtime(self.curtime)
            # print "calling parseFile(lio=%s ignore_sections=%s,
            # utime_only=%s)"%(lio,ignore_sections,utime_only)
            changed = self.parseFile(lio, ignore_sections, utime_only)

            # delete temporary files
            del self.curtime
            del self.curtimelist

            # update the cache if necessary
            if changed:
                lio.update()
        finally:
            lio.close()

    #***********************************************************
    # Leave only the jids that have had a change since prev_time
    def limit_to_recent(self, prev_time):
        for j in self.jids.keys():
            new_events = self.get_new_events(self.jids[j], prev_time)
            if len(new_events.keys()) == 0:
                del self.jids[j]  # nothing changed, remove
            else:
                self.jids[j]['new_events'] = new_events  # list changes

    #****************************************
    def write(self, long=0):
        schedd = os.environ.get("SCHEDD", socket.gethostname())
        jids = sorted(self.jids.keys())
        for jid in jids:
            el = self.jids[jid]
            if long == 2:
                print "jid=%s el=%s el[keys]=%s" % (jid, el, el.keys())
            cur = status_strings[el["current"]]
            if cur == "Completed":
                cur = cur + " Exit Code:%s" % el["end"]["retcode"]
            print "JobsubJobID: %s.0@%s %s DAGNodeName: %s" % (jid, schedd, cur, el["section"])
            if long:
                print "\tSubmitted: %s %s" % (el["submit"]["date"], el["submit"]["time"])
                if "exe" in el:
                    print "\tExe on %s: %s %s " % (socket.gethostbyaddr(el["exe"]["node"])[0], el["exe"]["date"], el["exe"]["time"])
                if "end" in el:
                    print "\tDone Exit Code %s: %s %s" % (el["end"]["retcode"], el["end"]["date"], el["end"]["time"])
                if "abort" in el:
                    print "\tAbort: %s %s" % (el["abort"]["date"], el["abort"]["time"])

    ##########################################################################
    xmldesc_jids = {'class': {}}

    def xml_jids(self, tag_name='jids', indent_tab="   ", leading_tab=""):
        return xml_format.dict2string(self.jids,
                                      tag_name, 'jid',
                                      indent_tab=indent_tab, leading_tab=leading_tab,
                                      subtypes_params=self.xmldesc_jids)

    def xmlwrite_jids(self, fd, tag_name='jids',
                      indent_tab="   ", leading_tab=""):
        return xml_format.dict2file(file, self.jids,
                                    tag_name, 'jid',
                                    indent_tab=indent_tab, leading_tab=leading_tab,
                                    subtypes_params=self.xmldesc_jids)

    ##########################################################################
    def xml_sections(self, tag_name='sections',
                     indent_tab="   ", leading_tab=""):
        return xml_format.dict2string(self.sections,
                                      tag_name, 'section',
                                      indent_tab=indent_tab, leading_tab=leading_tab,
                                      el_attr_name='jid')

    def xmlwrite_sections(self, fd, tag_name='sections',
                          indent_tab="   ", leading_tab=""):
        return xml_format.dict2file(fd, self.sections,
                                    tag_name, 'section',
                                    indent_tab=indent_tab, leading_tab=leading_tab,
                                    el_attr_name='jid')

# Usually one attribute:
#   jids - dictionary of Condor JobIDs, each having the status of the job (any status_code)
# If want_counters is specified, a second attribute is added:
#   counters - dictionary of Condor JobIDs, containing a discrionary of states
#                   each element count how many times it went throug that state


class DAGManLogParserFast:

    def parseFile(self, fd, want_counters, alive_only):
        changed = 0

        i = 0
        block_nr = 0
        while True:
            line = fd.readline()
            if len(line) == 0:
                return changed  # EOF

            #optypestr,jidstr,other = string.split(line," ",2)
            try:
                optype = int(line[0:3])
                jid = int(string.split(line[5:15], '.', 1)[0])
            except:
                # in case of error, just skip (optype=-1)
                optype = -1
                jid = 0
            new_state = None
            if optype in (0,   # submit
                          4,  # evict
                          7,  # shadow exception
                          13,  # release
                          24):  # connection lost
                new_state = 1  # status_codes["Idle"]
            elif optype in (1,  # Execute
                            11):  # Unsuspend
                new_state = 2  # status_codes["Running"]
            elif optype == 5:  # done
                if jid in self.jids and (self.jids[jid] != 2):
                    # never really run, assume fake event for removing
                    new_state = 3  # status_codes["Removed"]
                else:
                    new_state = 4  # status_codes["Completed"]
            elif optype == 9:  # abort
                new_state = 3  # status_codes["Removed"]
            elif optype == 10:  # suspend
                new_state = 6  # status_codes["Suspended"]
            elif optype == 12:  # hold
                new_state = 5  # status_codes["Held"]
            else:
                pass  # everything else can be safely ignored

            # split the text file in blocks
            j = i + 1
            line = fd.readline()
            while (len(line) > 0) and (line != "...\n"):
                j = j + 1
                line = fd.readline()

            if len(line) == 0:
                # EOF found, exit
                return changed
            # end of block found, update status
            fd.release()

            changed = 1
            if alive_only and (new_state in (3,  # removed
                                             4)):  # completed
                if jid in self.jids:
                    del self.jids[jid]
                if want_counters and jid in self.counters:
                    del self.counters[jid]
            elif new_state is not None:
                self.jids[jid] = new_state
                if want_counters:
                    if jid in self.counters:
                        cel = self.counters[jid]
                    else:
                        cel = {}

                    s = new_state
                    if s in cel:
                        cel[s] = cel[s] + 1
                    else:
                        cel[s] = 1

                    self.counters[jid] = cel

            # iterate
            i = j + 1
            block_nr = block_nr + 1

    # main
    #****************************************
    def __init__(self, logfilename, use_cache=0,
                 cache_dir=None, want_counters=0, alive_only=0):
        if want_counters:
            default_fields = {"jids": {}, "counters": {}}
        else:
            default_fields = {}

        if use_cache:
            if cache_dir is None:
                cache_basename = logfilename
            else:
                cache_basename = cache_dir + "/cache_" + \
                    string.replace(logfilename, "/", "_")
            ext = 'dmpf'
            if want_counters:
                ext = ext + 'c'
            if alive_only:
                ext = ext + 'a'

            ext = ext + 'i'  # because we now use LineIO
            #lio = DiskModule.CachedLineIO(logfilename,cache_basename+'.'+ext,default_fields)
        else:
            lio = LineIO(logfilename, default_fields)
        # the log files can be big, so use LineIO class
        lio.open()
        try:
            if want_counters:
                self.jids = lio.fields["jids"]
                self.counters = lio.fields["counters"]
            else:
                self.jids = lio.fields

            changed = self.parseFile(lio, want_counters, alive_only)

            # update the cache if necessary
            if changed:
                lio.update()
        finally:
            lio.close()

    ##########################################################################
    def xml_jids(self, tag_name='jid', indent_tab="   ", leading_tab=""):
        return xml_format.dict2string(self.jids,
                                      tag_name, 'jid',
                                      indent_tab=indent_tab, leading_tab=leading_tab)

    def xmlwrite_jids(self, fd, tag_name='jid',
                      indent_tab="   ", leading_tab=""):
        return xml_format.dict2file(fd, self.jids,
                                    tag_name, 'jid',
                                    indent_tab=indent_tab, leading_tab=leading_tab)


###########################################################################
# these ones will work on line by line basis
class LineIO:

    def __init__(self, filename, default_fields):
        self.filename = filename
        self.fields = default_fields

        self.fd = None
        self.released_pos = 0

    def open(self):
        self.fd = open(self.filename, "r")
        self.released_pos = 0

    def close(self):
        self.fd.close()

    def tell(self):
        return self.fd.tell()

    def tell_line(self):
        return self.first_line + len(self.cached_lines)

    def readline(self):
        return self.fd.readline()

    # call this function when you have used the lines up to this point
    # used to tell the cache where to start next time (for childs)
    def release(self):
        self.released_pos = self.fd.tell()

    def update(self):
        pass  # dummy
