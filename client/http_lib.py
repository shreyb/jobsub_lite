
def curl_secure_context(url, credentials):
    """
    Create a standard curl object for talking to http/https url set with most
    standard options used. Does not set client credentials.

    Returns the curl along with the response object
    """

    curl, response = curl_context(url)

    curl.setopt(curl.SSLCERT, credentials.get('cert'))
    curl.setopt(curl.SSLKEY, credentials.get('key'))
    proxy = credentials.get('proxy')
    if proxy:
        cmd = '/usr/bin/voms-proxy-info -type -file %s' % proxy
        cmd_out, cmd_err = subprocessSupport.iexe_cmd(cmd)
        if 'RFC compliant proxy' in cmd_out:
            logSupport.dprint("setting CAINFO for %s" % proxy)
            curl.setopt(curl.CAINFO, proxy)
    curl.setopt(curl.SSL_VERIFYHOST, constants.JOBSUB_SSL_VERIFYHOST)
    if platform.system() == 'Darwin':
        curl.setopt(curl.CAINFO, './ca-bundle.crt')
    else:
        curl.setopt(curl.CAPATH, get_capath())

    return (curl, response)


def curl_context(url):
    """
    Create a standard curl object for talking to https url set with most
    standard options used

    Returns the curl along with the response object
    """

    # Reponse from executing curl
    response = io.StringIO()

    # Create curl object and set curl options to use
    curl = pycurl.Curl()
    curl.setopt(curl.URL, str(url))
    curl.setopt(curl.FAILONERROR, False)
    curl.setopt(curl.TIMEOUT, constants.JOBSUB_PYCURL_TIMEOUT)
    curl.setopt(curl.CONNECTTIMEOUT, constants.JOBSUB_PYCURL_CONNECTTIMEOUT)
    curl.setopt(curl.WRITEFUNCTION, response.write)
    curl.setopt(curl.HTTPHEADER, ['Accept: application/json'])
    curl.setopt(curl.SSLVERSION, curl.SSLVERSION_TLSv1)

    return (curl, response)


def get_capath():
    ca_dir_list = ['/etc/grid-security/certificates',
                   '/cvmfs/oasis.opensciencegrid.org/mis/certificates',
                   '/cvmfs/grid.cern.ch/etc/grid-security/certificates',
                   ]
    ca_dir = os.environ.get('X509_CERT_DIR')

    if not ca_dir:
        for system_ca_dir in ca_dir_list:
            if (os.path.exists(system_ca_dir)):
                ca_dir = system_ca_dir
                break

    if not ca_dir:
        err = 'Could not find CA Certificates in %s. ' % system_ca_dir
        err += 'Set X509_CERT_DIR in the environment.'
        raise JobSubClientError(err)

    logSupport.dprint('Using CA_DIR: %s' % ca_dir)
    return ca_dir


def post_data_append(post_data, payload, fmt, fname):
    """
    append payload to HTTP post_data payload
    Params:
        @post_data: list of http post data objects
        @payload
        @fmt is postdata format
        @fname is file to append
    """
    try:
        assert(os.access(fname, os.R_OK))
        post_data.append((payload, (fmt, fname)))
        return post_data
    except Exception:
        raise JobSubClientError(
            "error HTTP POSTing %s - Is it readable?" %
            fname)

