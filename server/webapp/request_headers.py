
"""Module: request_headers
   Purpose: retrieve various information from http/cherrypy request headers
   Author:  Dennis Box, dbox@fnal.gov
"""
import cherrypy
import logger


def get_client_dn():
    """
    Identify the client DN based on if the client is using a X509 cert-key
    pair or an X509 proxy. Currently only works with a single proxy chain.
    Wont work if the proxy is derieved from the proxy itself.
    """

    issuer_dn = cherrypy.request.headers.get('Ssl-Client-I-Dn')
    client_dn = cherrypy.request.headers.get('Ssl-Client-S-Dn')

    # In case of proxy additional last part will be of the form /CN=[0-9]*
    # In other words, issuer_dn is a substring of the client_dn
    if client_dn.startswith(issuer_dn):
        client_dn = issuer_dn
    return client_dn


def path_info():
    """
    Returns a list of the path elements
    /jobsub/acctgroups/nova/jobs
    returns ['jobsub','acctgroups','nova','jobs']
    """
    path = cherrypy.request.path_info
    path = path.strip('/')
    p_list = path.split('/')
    return p_list


def path_end():
    """
    Returns last element in the path
    /jobsub/acctgroups/nova/jobs
    returns 'jobs'
     """

    p_list = path_info()
    return p_list[-1]
