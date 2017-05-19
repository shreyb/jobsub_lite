Name:           jobsub
Version:        __VERSION__
Release:        __RELEASE__
Summary:        RESTful API for Jobsub

Group:          Applications/System
License:        Fermitools Software Legal Information (Modified BSD License)
URL:            https://cdcvs.fnal.gov/redmine/projects/jobsub
Source0:        %{name}-%{version}.tar.gz
BuildRoot:      %(mktemp -ud %{_tmppath}/%{name}-%{version}-XXXXXX)

BuildArch:      noarch

Requires:       krb5-fermi-getcert
Requires:       voms-clients
Requires:       vo-client
Requires:       python-cherrypy >= 3.2.2
Requires:       condor-python
Requires:       openssl
Requires:       mod_ssl
Requires:       mod_wsgi
Requires:       osg-ca-scripts
Requires:       fetch-crl


%description
Jobsub Server REST API

%prep
%setup -q


%build


%install
# copy the files into place
mkdir -p $RPM_BUILD_ROOT/opt/jobsub
cp -r ./ $RPM_BUILD_ROOT/opt/jobsub
mkdir -p $RPM_BUILD_ROOT/etc/httpd/conf.d
mkdir -p $RPM_BUILD_ROOT/scratch/uploads
mkdir -p $RPM_BUILD_ROOT/scratch/dropbox
cp ./server/conf/jobsub_api.conf $RPM_BUILD_ROOT/etc/httpd/conf.d/jobsub_api.conf


%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%doc
%config(noreplace) /etc/httpd/conf.d/jobsub_api.conf
%config(noreplace) /opt/jobsub/server/conf/jobsub_api.conf
%config(noreplace) /opt/jobsub/server/conf/jobsub.ini
/opt/jobsub/lib/DAGParser/DAGManParser.py
/opt/jobsub/lib/DAGParser/DAGManParser.pyc
/opt/jobsub/lib/DAGParser/DAGManParser.pyo
/opt/jobsub/lib/DAGParser/PrintSummary.py
/opt/jobsub/lib/DAGParser/PrintSummary.pyc
/opt/jobsub/lib/DAGParser/PrintSummary.pyo
/opt/jobsub/lib/DAGParser/xml_format.py
/opt/jobsub/lib/DAGParser/xml_format.pyc
/opt/jobsub/lib/DAGParser/xml_format.pyo
/opt/jobsub/lib/groupsettings/__init__.py
/opt/jobsub/lib/groupsettings/__init__.pyc
/opt/jobsub/lib/groupsettings/__init__.pyo
/opt/jobsub/lib/groupsettings/JobSettings.py
/opt/jobsub/lib/groupsettings/JobSettings.pyo
/opt/jobsub/lib/groupsettings/JobSettings.pyc
/opt/jobsub/lib/groupsettings/JobUtils.py
/opt/jobsub/lib/groupsettings/JobUtils.pyo
/opt/jobsub/lib/groupsettings/JobUtils.pyc
/opt/jobsub/lib/groupsettings/CdfSettings.py
/opt/jobsub/lib/groupsettings/CdfSettings.pyo
/opt/jobsub/lib/groupsettings/CdfSettings.pyc
/opt/jobsub/lib/groupsettings/MinervaSettings.py
/opt/jobsub/lib/groupsettings/MinervaSettings.pyo
/opt/jobsub/lib/groupsettings/MinervaSettings.pyc
/opt/jobsub/lib/groupsettings/MinosSettings.py
/opt/jobsub/lib/groupsettings/MinosSettings.pyc
/opt/jobsub/lib/groupsettings/MinosSettings.pyo
/opt/jobsub/lib/groupsettings/NovaSettings.py
/opt/jobsub/lib/groupsettings/NovaSettings.pyo
/opt/jobsub/lib/groupsettings/NovaSettings.pyc
/opt/jobsub/lib/JobsubConfigParser/fakelogger.py
/opt/jobsub/lib/JobsubConfigParser/fakelogger.pyc
/opt/jobsub/lib/JobsubConfigParser/fakelogger.pyo
/opt/jobsub/lib/JobsubConfigParser/__init__.py
/opt/jobsub/lib/JobsubConfigParser/__init__.pyc
/opt/jobsub/lib/JobsubConfigParser/__init__.pyo
/opt/jobsub/lib/JobsubConfigParser/JobsubConfigParser.py
/opt/jobsub/lib/JobsubConfigParser/JobsubConfigParser.pyc
/opt/jobsub/lib/JobsubConfigParser/JobsubConfigParser.pyo
/opt/jobsub/lib/logger/__init__.py
/opt/jobsub/lib/logger/__init__.pyc
/opt/jobsub/lib/logger/__init__.pyo
/opt/jobsub/lib/logger/logger.py
/opt/jobsub/lib/logger/logger.pyc
/opt/jobsub/lib/logger/logger.pyo
/opt/jobsub/LICENSE.txt
/opt/jobsub/server/__init__.py
/opt/jobsub/server/__init__.pyc
/opt/jobsub/server/__init__.pyo
/opt/jobsub/server/admin/fill_jobsub_history.py
/opt/jobsub/server/admin/fill_jobsub_history.pyc
/opt/jobsub/server/admin/fill_jobsub_history.pyo
/opt/jobsub/server/admin/fill_jobsub_history.sh
/opt/jobsub/server/admin/fix_sandbox_links.py
/opt/jobsub/server/admin/fix_sandbox_links.pyc
/opt/jobsub/server/admin/fix_sandbox_links.pyo
/opt/jobsub/server/admin/fix_sandbox_links.sh
/opt/jobsub/server/admin/jobsub_preen.py
/opt/jobsub/server/admin/jobsub_preen.pyc
/opt/jobsub/server/admin/jobsub_preen.pyo
/opt/jobsub/server/admin/jobsub_preen.sh
/opt/jobsub/server/admin/krbrefresh.sh
/opt/jobsub/server/admin/test_krbrefresh.sh
/opt/jobsub/server/tools/dagsub
/opt/jobsub/server/tools/jobsub
/opt/jobsub/server/tools/returnOK.sh
/opt/jobsub/server/tools/summary.sh
/opt/jobsub/server/webapp/jobsub_priv
/opt/jobsub/server/webapp/__init__.py
/opt/jobsub/server/webapp/__init__.pyc
/opt/jobsub/server/webapp/__init__.pyo
/opt/jobsub/server/webapp/accounting_group.py
/opt/jobsub/server/webapp/accounting_group.pyc
/opt/jobsub/server/webapp/accounting_group.pyo
/opt/jobsub/server/webapp/auth.py
/opt/jobsub/server/webapp/auth.pyc
/opt/jobsub/server/webapp/auth.pyo
/opt/jobsub/server/webapp/auth_myproxy.py
/opt/jobsub/server/webapp/auth_myproxy.pyc
/opt/jobsub/server/webapp/auth_myproxy.pyo
/opt/jobsub/server/webapp/auth_gums.py
/opt/jobsub/server/webapp/auth_gums.pyc
/opt/jobsub/server/webapp/auth_gums.pyo
/opt/jobsub/server/webapp/auth_kca.py
/opt/jobsub/server/webapp/auth_kca.pyc
/opt/jobsub/server/webapp/auth_kca.pyo
/opt/jobsub/server/webapp/auth_methods.py
/opt/jobsub/server/webapp/auth_methods.pyc
/opt/jobsub/server/webapp/auth_methods.pyo
/opt/jobsub/server/webapp/authutils.py
/opt/jobsub/server/webapp/authutils.pyc
/opt/jobsub/server/webapp/authutils.pyo
/opt/jobsub/server/webapp/better_analyze.py
/opt/jobsub/server/webapp/better_analyze.pyc
/opt/jobsub/server/webapp/better_analyze.pyo
/opt/jobsub/server/webapp/by_user.py
/opt/jobsub/server/webapp/by_user.pyc
/opt/jobsub/server/webapp/by_user.pyo
/opt/jobsub/server/webapp/condor_commands.py
/opt/jobsub/server/webapp/condor_commands.pyc
/opt/jobsub/server/webapp/condor_commands.pyo
/opt/jobsub/server/webapp/configured_sites.py
/opt/jobsub/server/webapp/configured_sites.pyc
/opt/jobsub/server/webapp/configured_sites.pyo
/opt/jobsub/server/webapp/constraint.py
/opt/jobsub/server/webapp/constraint.pyc
/opt/jobsub/server/webapp/constraint.pyo
/opt/jobsub/server/webapp/dag.py
/opt/jobsub/server/webapp/dag.pyc
/opt/jobsub/server/webapp/dag.pyo
/opt/jobsub/server/webapp/dag_help.py
/opt/jobsub/server/webapp/dag_help.pyc
/opt/jobsub/server/webapp/dag_help.pyo
/opt/jobsub/server/webapp/dropbox.py
/opt/jobsub/server/webapp/dropbox.pyc
/opt/jobsub/server/webapp/dropbox.pyo
/opt/jobsub/server/webapp/forcex_jobid.py
/opt/jobsub/server/webapp/forcex_jobid.pyc
/opt/jobsub/server/webapp/forcex_jobid.pyo
/opt/jobsub/server/webapp/format.py
/opt/jobsub/server/webapp/format.pyc
/opt/jobsub/server/webapp/format.pyo
/opt/jobsub/server/webapp/history.py
/opt/jobsub/server/webapp/history.pyc
/opt/jobsub/server/webapp/history.pyo
/opt/jobsub/server/webapp/ifront_q.sh
/opt/jobsub/server/webapp/job.py
/opt/jobsub/server/webapp/job.pyc
/opt/jobsub/server/webapp/job.pyo
/opt/jobsub/server/webapp/jobid.py
/opt/jobsub/server/webapp/jobid.pyc
/opt/jobsub/server/webapp/jobid.pyo
/opt/jobsub/server/webapp/jobsub.py
/opt/jobsub/server/webapp/jobsub.pyc
/opt/jobsub/server/webapp/jobsub.pyo
/opt/jobsub/server/webapp/jobsub_api.py
/opt/jobsub/server/webapp/jobsub_api.pyc
/opt/jobsub/server/webapp/jobsub_api.pyo
/opt/jobsub/server/webapp/jobsub_dag_runner.sh
/opt/jobsub/server/webapp/jobsub_env_runner.sh
/opt/jobsub/server/webapp/jobsub_help.py
/opt/jobsub/server/webapp/jobsub_help.pyc
/opt/jobsub/server/webapp/jobsub_help.pyo
/opt/jobsub/server/webapp/queued_outformat.py
/opt/jobsub/server/webapp/queued_outformat.pyc
/opt/jobsub/server/webapp/queued_outformat.pyo
/opt/jobsub/server/webapp/queued_jobs.py
/opt/jobsub/server/webapp/queued_jobs.pyc
/opt/jobsub/server/webapp/queued_jobs.pyo
/opt/jobsub/server/webapp/queued_jobstatus.py
/opt/jobsub/server/webapp/queued_jobstatus.pyc
/opt/jobsub/server/webapp/queued_jobstatus.pyo
/opt/jobsub/server/webapp/request_headers.py
/opt/jobsub/server/webapp/request_headers.pyc
/opt/jobsub/server/webapp/request_headers.pyo
/opt/jobsub/server/webapp/sandbox.py
/opt/jobsub/server/webapp/sandbox.pyc
/opt/jobsub/server/webapp/sandbox.pyo
/opt/jobsub/server/webapp/sandboxes.py
/opt/jobsub/server/webapp/sandboxes.pyc
/opt/jobsub/server/webapp/sandboxes.pyo
/opt/jobsub/server/webapp/sqlite_commands.py
/opt/jobsub/server/webapp/sqlite_commands.pyc
/opt/jobsub/server/webapp/sqlite_commands.pyo
/opt/jobsub/server/webapp/scheddload.py
/opt/jobsub/server/webapp/scheddload.pyc
/opt/jobsub/server/webapp/scheddload.pyo
/opt/jobsub/server/webapp/subprocessSupport.py
/opt/jobsub/server/webapp/subprocessSupport.pyc
/opt/jobsub/server/webapp/subprocessSupport.pyo
/opt/jobsub/server/webapp/summary.py
/opt/jobsub/server/webapp/summary.pyc
/opt/jobsub/server/webapp/summary.pyo
/opt/jobsub/server/webapp/users.py
/opt/jobsub/server/webapp/users.pyc
/opt/jobsub/server/webapp/users.pyo
/opt/jobsub/server/webapp/users_jobs.py
/opt/jobsub/server/webapp/users_jobs.pyc
/opt/jobsub/server/webapp/users_jobs.pyo
/opt/jobsub/server/webapp/util.py
/opt/jobsub/server/webapp/util.pyc
/opt/jobsub/server/webapp/util.pyo
/opt/jobsub/server/webapp/version.py
/opt/jobsub/server/webapp/version.pyc
/opt/jobsub/server/webapp/version.pyo
/scratch/dropbox/
/scratch/uploads/

%changelog

* Mon Apr 18 2016 Parag Mhashilkar <parag@fnal.gov> - 1.0.2-2
- Changed the dependency from osg-ca-certs to osg-ca-scripts on operations request

* Wed Dec 10 2014 Parag Mhashilkar <parag@fnal.gov> - 1.0.4-1
- Jobsub version v1.0.4

* Fri Oct 30 2014 Parag Mhashilkar <parag@fnal.gov> - 1.0.3-1
- Jobsub version v1.0.3

* Fri Oct 24 2014 Parag Mhashilkar <parag@fnal.gov> - 1.0.2-1
- Jobsub version v1.0.2

* Wed Oct 1 2014 Parag Mhashilkar <parag@fnal.gov> - 1.0.1-1
- Jobsub version v1.0.1

* Wed Sep 10 2014 Parag Mhashilkar <parag@fnal.gov> - 1.0-1
- Jobsub version v1.0

* Thu Jul 31 2014 Parag Mhashilkar <parag@fnal.gov> - 0.4-1
- Jobsub version v0.4

* Tue Jun 10 2014 Dennis Box <dbox@fnal.gov> - 0.3.1.1-1
- Jobsub version v0.3.1.1 - bugfix for v0.3.1

* Wed Jun 04 2014 Parag Mhashilkar <parag@fnal.gov> - 0.3.1-1
- Jobsub version v0.3.1

* Fri May 23 2014 Parag Mhashilkar <parag@fnal.gov> - 0.3-1
- Jobsub version v0.3. Support for HA.

* Wed Apr 16 2014 Dennis Box <dbox@fnal.gov> - 0.2.1-1
- Jobsub version v0.2.1

* Wed Apr 02 2014 Dennis Box <dbox@fnal.gov> - 0.2-1
- Jobsub version v0.2

* Thu Feb 27 2014 Dennis Box <dbox@fnal.gov> - 0.1.4-2
- fixed some dropbox directory issues

* Wed Jan 29 2014 Dennis Box <dbox@fnal.gov> - 0.1.2.1-1
- Changed dependency from osg-ca-scripts to osg-ca-certs

* Wed Jan 15 2014 Dennis Box <dbox@fnal.gov> - 0.1.2-1
- jobSub Server webap v0.1.2

* Mon Dec 23 2013 Parag Mhashilkar <parag@fnal.gov> - 0.1.1-1
- jobSub Server webapp v0.1.1

* Fri Dec 13 2013 Parag Mhashilkar <parag@fnal.gov> - 0.1-1
- First version of the JobSub server
