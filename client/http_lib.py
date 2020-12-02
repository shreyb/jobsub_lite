import os
import sys
import traceback
import pycurl
import platform
import six
import logSupport
import constants
import subprocessSupport

class HTTPLibError(Exception):

    def __init__(self, errMsg="http call failed."):
        logSupport.dprint(traceback.format_exc())
        sys.exit(errMsg)

def curl_secure_context(url, credentials):
    """
    Create a standard curl object for talking to http/https url set with most
    standard options used. Does not set client credentials.

    Returns the curl along with the response object
    """

    curl, response = curl_context(url)

    curl.setopt(curl.SSLCERT, coerce_str(credentials.get('cert')))
    curl.setopt(curl.SSLKEY, coerce_str(credentials.get('key')))
    proxy = credentials.get('proxy')
    if proxy:
        cmd = '/usr/bin/voms-proxy-info -type -file %s' % proxy
        cmd_out, cmd_err = subprocessSupport.iexe_cmd(cmd)
        if 'RFC compliant proxy' in cmd_out:
            logSupport.dprint("setting CAINFO for %s" % proxy)
            curl.setopt(curl.CAINFO, proxy)
    curl.setopt(curl.SSL_VERIFYHOST, constants.JOBSUB_SSL_VERIFYHOST)
    return (curl, response)


def curl_context(url):
    """
    Create a standard curl object for talking to https url set with most
    standard options used

    Returns the curl along with the response object
    """

    # Reponse from executing curl
    response = six.BytesIO()


    # Create curl object and set curl options to use
    curl = pycurl.Curl()
    curl.setopt(curl.URL, str(url))
    curl.setopt(curl.FAILONERROR, False)
    curl.setopt(curl.TIMEOUT, constants.JOBSUB_PYCURL_TIMEOUT)
    curl.setopt(curl.CONNECTTIMEOUT, constants.JOBSUB_PYCURL_CONNECTTIMEOUT)
    curl.setopt(curl.WRITEFUNCTION, response.write)
    curl.setopt(curl.HTTPHEADER, ['Accept: application/json'])
    curl.setopt(curl.SSLVERSION, curl.SSLVERSION_TLSv1)
    if logSupport.DEBUG_MODE:
        curl.setopt(curl.VERBOSE, 1)
    if platform.system() == 'Darwin':
        curl.setopt(curl.CAINFO, './ca-bundle.crt')
    else:
        curl.setopt(curl.CAPATH, coerce_str(get_capath()))


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
        raise HTTPLibError(err)

    logSupport.dprint('Using CA_DIR: %s' % ca_dir)
    return ca_dir

def curl_setopt_str(a_curl, an_opt, a_type):
    a_curl.setopt(an_opt, coerce_str(a_type))

def coerce_str(a_str):
    a_str = six.b(str(a_str))
    #logSupport.dprint('coerce_str returns %s' % a_str)
    return a_str

def post_data_append(post_data, item_descr, in_data, fmt=None):
    """
    append item_descr to HTTP post_data item_descr
    Params:
        @post_data: list of http post data objects
        @item_descr
        @in_data string or file to append
        @fmt is postdata format
    Returns:
        post_data appended with input
    """
    #import pdb; pdb.set_trace()
    if not fmt:
        post_data.append((coerce_str(item_descr), coerce_str(in_data)))
        logSupport.dprint('post_data=%s'% post_data)
        return post_data
    else:
        try:
            assert(os.access(in_data, os.R_OK))
            post_data.append((coerce_str(item_descr),
                              (fmt, coerce_str(in_data))))
            #logSupport.dprint('post_data=%s'% post_data)
            return post_data
        except Exception:
            raise RuntimeError(
                "error HTTP POSTing %s - Is it readable?" %
                in_data)

