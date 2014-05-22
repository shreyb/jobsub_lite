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

Requires:       krb5-workstation
Requires:       krb5-fermi-getcert
Requires:       voms-clients
Requires:       vo-client
Requires:       python-cherrypy >= 3.2.2
Requires:       condor-python
Requires:       openssl
Requires:       mod_ssl
Requires:       mod_wsgi
Requires:       osg-ca-certs
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
/opt/jobsub/LICENSE.txt
/opt/jobsub/lib/JobsubConfigParser/JobsubConfigParser.py
/opt/jobsub/lib/JobsubConfigParser/JobsubConfigParser.pyc
/opt/jobsub/lib/JobsubConfigParser/JobsubConfigParser.pyo
/opt/jobsub/lib/JobsubConfigParser/fakelogger.py
/opt/jobsub/lib/JobsubConfigParser/fakelogger.pyc
/opt/jobsub/lib/JobsubConfigParser/fakelogger.pyo
/opt/jobsub/lib/JobsubConfigParser/__init.py__
/opt/jobsub/lib/logger/__init__.py
/opt/jobsub/lib/logger/__init__.pyc
/opt/jobsub/lib/logger/__init__.pyo
/opt/jobsub/lib/logger/logger.py
/opt/jobsub/lib/logger/logger.pyc
/opt/jobsub/lib/logger/logger.pyo
/opt/jobsub/server/__init__.py
/opt/jobsub/server/__init__.pyc
/opt/jobsub/server/__init__.pyo
/opt/jobsub/server/webapp/__init__.py
/opt/jobsub/server/webapp/__init__.pyc
/opt/jobsub/server/webapp/__init__.pyo
/opt/jobsub/server/webapp/accounting_group.py
/opt/jobsub/server/webapp/accounting_group.pyc
/opt/jobsub/server/webapp/accounting_group.pyo
/opt/jobsub/server/webapp/auth.py
/opt/jobsub/server/webapp/auth.pyc
/opt/jobsub/server/webapp/auth.pyo
/opt/jobsub/server/webapp/format.py
/opt/jobsub/server/webapp/format.pyc
/opt/jobsub/server/webapp/format.pyo
/opt/jobsub/server/webapp/job.py
/opt/jobsub/server/webapp/job.pyc
/opt/jobsub/server/webapp/job.pyo
/opt/jobsub/server/webapp/jobsub.py
/opt/jobsub/server/webapp/jobsub.pyc
/opt/jobsub/server/webapp/jobsub.pyo
/opt/jobsub/server/webapp/jobsub_api.py
/opt/jobsub/server/webapp/jobsub_api.pyc
/opt/jobsub/server/webapp/jobsub_api.pyo
/opt/jobsub/server/webapp/jobsub_env_runner.sh
/opt/jobsub/server/webapp/subprocessSupport.py
/opt/jobsub/server/webapp/subprocessSupport.pyc
/opt/jobsub/server/webapp/subprocessSupport.pyo
/opt/jobsub/server/webapp/condor_commands.py
/opt/jobsub/server/webapp/condor_commands.pyc
/opt/jobsub/server/webapp/condor_commands.pyo
/opt/jobsub/server/webapp/sandbox.py
/opt/jobsub/server/webapp/sandbox.pyc
/opt/jobsub/server/webapp/sandbox.pyo
/opt/jobsub/server/webapp/queued_jobs.py
/opt/jobsub/server/webapp/queued_jobs.pyc
/opt/jobsub/server/webapp/queued_jobs.pyo
/opt/jobsub/server/webapp/users.py
/opt/jobsub/server/webapp/users.pyc
/opt/jobsub/server/webapp/users.pyo
/opt/jobsub/server/webapp/history.py
/opt/jobsub/server/webapp/history.pyc
/opt/jobsub/server/webapp/history.pyo
/opt/jobsub/server/webapp/util.py
/opt/jobsub/server/webapp/util.pyc
/opt/jobsub/server/webapp/util.pyo
/opt/jobsub/server/admin/krbrefresh.sh
/opt/jobsub/server/admin/test_krbrefresh.sh
/opt/jobsub/server/admin/fix_sandbox_links.py
/opt/jobsub/server/admin/fix_sandbox_links.pyc
/opt/jobsub/server/admin/fix_sandbox_links.pyo
/opt/jobsub/server/admin/fix_sandbox_links.sh
/scratch/uploads/
/scratch/dropbox/

%changelog
* Thu May 22 2014 Parag Mhashilkar <parag@fnal.gov> - 0.3.0-0.4.rc4
- Jobsub version v0.3.rc4

* Wed May 21 2014 Dennis Box <dbox@fnal.gov> - 0.3.0-0.3.rc3
- Jobsub version v0.3.rc3

* Mon May 12 2014 Parag Mhashilkar <parag@fnal.gov> - 0.3.0-0.1.rc1
- Jobsub version v0.3.rc1

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
