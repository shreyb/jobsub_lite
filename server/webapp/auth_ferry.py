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
import jobsub
import subprocessSupport
import authutils
import util


def authenticate(dn, acctgroup, acctrole):
    """Check if this combination in ferry database
       Args:
                  dn: DN of proxy or cert trying to authenticate
           acctgroup: accounting group (experiment)
            acctrole: role (Analysis, Production, etc)
    """
    try:
        logger.log('acctgroup=%s, acctrole=%s'%(acctgroup, acctrole))
        fqan = get_ferry_fqan(acctgroup, acctrole)
        
        logger.log('fqan=%s'%(fqan))
        username = get_ferry_mapping(dn, fqan)
        username = username.strip()
        logger.log("ferry mapped dn '%s' fqan '%s' to '%s'" %
                   (dn, fqan, username))
        return username
    except:
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
    if fqan not in fqan_list(default_user(dn)):
        return None

    #vo_dat_file = "/var/lib/jobsub/ferry/vorolemapfile2.json"
    #dn_dat_file = "/var/lib/jobsub/ferry/gridmapfile2.json"
    vo_dat_file = "fqan_user_map.json"
    dn_dat_file = "dn_user_roles_map.json"
    vo_dat = util.json_from_file(vo_dat_file)
    dn_dat = util.json_from_file(dn_dat_file)
    dn_map = dn_dat.get(dn)
    vo_map = vo_dat.get(fqan)
    if dn_map:
        if vo_map:
            return vo_map
        else:
            return dn_map['mapped_uname']['default']
    return None

def default_user(dn):
    default_user = None
    #dn_dat_file = "/var/lib/jobsub/ferry/gridmapfile2.json"
    dn_dat_file = "dn_user_roles_map.json"
    dn_dat = util.json_from_file(dn_dat_file)
    dn_map = dn_dat.get(dn)
    if dn_map:
        default_user = dn_map['mapped_uname']['default']
    return default_user

def vos_for_dn(dn):
    vo_list = []
    #dn_dat_file = "/var/lib/jobsub/ferry/gridmapfile2.json"
    dn_dat_file = "dn_user_roles_map.json"
    dn_dat = util.json_from_file(dn_dat_file)
    dn_map = dn_dat.get(dn)
    if dn_map:
        vo_list = dn_map['volist']
    return vo_list


def fqan_list(uname):
     #aff_file = "/var/lib/jobsub/ferry/membersaffiliationsroles2.json"
     aff_file = "uname_fqan_map.json"
     aff_dat = util.json_from_file(aff_file)
     aff_list = aff_dat.get(uname)
     return aff_list

def alt_uname(fqan):
     #alt_uname_file =  "/var/lib/jobsub/ferry/vorolemapfile2.json"
     alt_uname_file =  "fqan_uname_map.json"
     alt_uname_dat = util.json_from_file(alt_uname_file)
     alt_unm = alt_uname_dat.get(fqan)
     return alt_unm


def get_ferry_fqan(acctgroup, acctrole=None):
    """return the fqan and mapped_uid for the role from ferry
    """
    #should not be hardcoded, obviously
    #vo_dat_file = "/var/lib/jobsub/ferry/vorolemapfile3.json"
    fqan = None
    try:
        vo_dat_file = "vo_role_fqan_map.json"
        vo_dat = util.json_from_file(vo_dat_file)
        vo_dict = vo_dat.get(acctgroup)
        if vo_dict:
            fqan = vo_dict.get('Role=%s'%acctrole)
    except Exception as e:
        logger.log(e,traceback=True)
    return fqan

if __name__ == '__main__':
    """
    """
    #gmaps = util.json_from_file('/var/lib/jobsub/ferry/gridmapfile3.json')
    gmaps = util.json_from_file("dn_user_roles_map.json")

    for dn in gmaps:
        uname = default_user(dn)
        vo_list = vos_for_dn(dn)
        fq_list = fqan_list(uname)
        print 'dn=%s maps to %s' %(dn,uname)
        print 'vos:%s fqans:%s' %(vo_list, fq_list)
        if fq_list:
            for fq in fq_list:
                print "%s %s"%(fq,get_ferry_mapping(dn,fq))
