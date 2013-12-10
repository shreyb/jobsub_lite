%if 0%{?rhel} && 0%{?rhel} <= 5
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

Name:           jobsub
Version:        1.0
Release:        0
Summary:        RESTful API for Jobsub

Group:          Applications/System
License:        Apache 2.0
URL:            https://cdcvs.fnal.gov/redmine/projects/jobsub
Source0:        %{name}-%{version}.tar.gz
BuildRoot:      %(mktemp -ud %{_tmppath}/%{name}-%{version}-XXXXXX)

BuildArch:      noarch

Requires:       python-cherrypy >= 3.1.2
Requires:       openssl
Requires:       mod_ssl
Requires:       mod_wsgi


%description
Jobsub API installation package for web

%prep
%setup -q


%build


%install
# copy the files into place
mkdir -p $RPM_BUILD_ROOT/opt/jobsub
cp -r ./ $RPM_BUILD_ROOT/opt/jobsub
mkdir -p $RPM_BUILD_ROOT/etc/httpd/conf.d
cp ./server/conf/jobsub_api.conf $RPM_BUILD_ROOT/etc/httpd/conf.d


%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%doc
/opt/jobsub/lib/JobsubConfigParser/JobsubConfigParser.py
/opt/jobsub/lib/JobsubConfigParser/JobsubConfigParser.pyc
/opt/jobsub/lib/JobsubConfigParser/JobsubConfigParser.pyo
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
/opt/jobsub/server/conf/jobsub.ini
/opt/jobsub/server/conf/jobsub_api.conf
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
/opt/jobsub/server/webapp/util.py
/opt/jobsub/server/webapp/util.pyc
/opt/jobsub/server/webapp/util.pyo
/etc/httpd/conf.d/jobsub_api.conf
