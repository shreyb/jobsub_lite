#!/usr/bin/env python
"""
 Description:
   This module implements the JobSub ferry  authN/authZ functionailty.

 Project:
   JobSub

 Author:
   Dennis Box

"""

import logger
import logging
import authutils


def authenticate(dn, acctgroup, acctrole):
    """Check if this combination in ferry database
       Args:
                  dn: DN of proxy or cert trying to authenticate
           acctgroup: accounting group (experiment)
            acctrole: role (Analysis, Production, etc)
    """
    try:
        logger.log('acctgroup=%s, acctrole=%s' % (acctgroup, acctrole))
        fqan = get_ferry_fqan(acctgroup, acctrole)
        logger.log('fqan=%s' % (fqan))
        username = get_ferry_mapping(dn, fqan)
        username = username.strip()
        logger.log("ferry mapped dn '%s' fqan '%s' to '%s'" %
                   (dn, fqan, username))
        return username
    except Exception:
        err = "ferry mapping for the dn '%s' fqan '%s' failed" % (dn, fqan)
        logger.log(err, traceback=True, severity=logging.ERROR)
        logger.log(err, traceback=True,
                   severity=logging.ERROR, logfile='error')
    raise authutils.AuthenticationError(dn, acctgroup)


def get_ferry_mapping(dn, fqan):
    """find user mapped to input combo
       Args:
             dn: DN of proxy or cert trying to authenticate
           fqan: combination of acctgroup/role
    """
    # getVORoleMapFile was changed. Before, a fqan could be present
    # and return an empty string.  Now, the fqan is not
    # present if it doesn't map to anything.  This check
    # needs to come out as a consequence
    #
    # if fqan not in fqan_list(default_user(dn)):
    #     return None
    dn = authutils.clean_proxy_dn(dn)
    vo_dat_file = "fqan_user_map.json"
    dn_dat_file = "dn_user_roles_map.json"
    vo_dat = authutils.json_from_file(vo_dat_file)
    dn_dat = authutils.json_from_file(dn_dat_file)
    dn_map = dn_dat.get(dn)
    vo_map = vo_dat.get(fqan)
    if dn_map:
        if vo_map:
            return vo_map
        else:
            return dn_map['mapped_uname']['default']
    return None


def default_user(dn):
    """
    Find  the 'default' user mapped to a dn

    Args:   dn: the registered dn of the user example
      "/DC=org/DC=cilogon/C=US/O=Fermi National Accelerator Laboratory/OU=People/CN=Marie Herman/CN=UID:mherman"
    Returns:
       mapped user name in this case: mherman
    """

    default_user = None
    dn_dat_file = "dn_user_roles_map.json"
    dn_dat = authutils.json_from_file(dn_dat_file)
    dn_map = dn_dat.get(dn)
    if dn_map:
        default_user = dn_map['mapped_uname']['default']
    return default_user


def vos_for_dn(dn):
    """ Return a list of VOs associated with a dn
    Args: dn a registered dn the ferry server knows about
    Returns: a python list i.e [ "nova", "cms", "dune"] associated with dn
    """

    vo_list = []
    dn_dat_file = "dn_user_roles_map.json"
    dn_dat = authutils.json_from_file(dn_dat_file)
    dn_map = dn_dat.get(dn)
    if dn_map:
        vo_list = dn_map['volist']
    return vo_list


def fqan_list(uname):
    """ return a list of fqans from ferry
    Args: uname a uid
    Returns: python list of fqans associated with that uname according to ferry server
    example     "stjohn": [
                           "/fermilab/lariat/Role=None",
                           "/fermilab/lariat/Role=Analysis",
                            "/fermilab/lariat/Role=Production",
                            "/fermilab/lariat/Role=Raw",
                            "/fermilab/uboone/Role=None",
                            "/fermilab/uboone/Role=Analysis",
                            "/fermilab/Role=None",
                            "/fermilab/Role=Analysis"
                            ]
    """
    aff_file = "uname_fqan_map.json"
    aff_dat = authutils.json_from_file(aff_file)
    aff_list = aff_dat.get(uname)
    return aff_list


def alt_uname(fqan):
    """return uid associated with fqan to override default user name
    Args: fqan
    Returns:uid
    example  fqan->"/fermilab/nova/Role=Production"
             returns->"novapro"
    """
    alt_uname_file = "fqan_uname_map.json"
    alt_uname_dat = authutils.json_from_file(alt_uname_file)
    alt_unm = alt_uname_dat.get(fqan)
    return alt_unm


def get_ferry_fqan(acctgroup, acctrole=None):
    """return the fqan and mapped_uid for the role from ferry
    """
    fqan = None
    try:
        vo_dat_file = "vo_role_fqan_map.json"
        vo_dat = authutils.json_from_file(vo_dat_file)
        vo_dict = vo_dat.get(acctgroup)
        if vo_dict:
            fqan = vo_dict.get('Role=%s' % acctrole)
    except Exception as e:
        logger.log(e, traceback=True)
    return fqan


if __name__ == '__main__':
    """
    test code
    """
    _gmaps = authutils.json_from_file("dn_user_roles_map.json")

    for _dn in _gmaps:
        _uname = default_user(_dn)
        _vo_list = vos_for_dn(_dn)
        _fq_list = fqan_list(_uname)
        print 'dn=%s maps to %s' % (_dn, _uname)
        print 'vos:%s fqans:%s' % (_vo_list, _fq_list)
        if _fq_list:
            for _fq in _fq_list:
                print "%s %s" % (_fq, get_ferry_mapping(_dn, _fq))
