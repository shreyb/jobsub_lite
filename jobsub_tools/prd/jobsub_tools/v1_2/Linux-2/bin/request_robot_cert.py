#!/usr/bin/env python
# $Id$
# Modified to request VO group and MARS software 6-15-2011 J Urish

import os
import string
import sys
import readline
import commands
import pexpect
import smtplib
from email.MIMEText import MIMEText


def webalyze( a_str):
    a_str=a_str.replace('=','%3D')
    a_str=a_str.replace(' ','+')
    a_str=a_str.replace("'","%27")
    a_str=a_str.replace('"',"%22")
    a_str=a_str.replace(',',"%2C")
    a_str=a_str.replace('-',"%2D")
    a_str=a_str.replace('.',"%2E")
    a_str=a_str.replace('/','%2F')
    return a_str

def make_new_dn(host_str):
    (retVal,val)=commands.getstatusoutput("kx509")
    lines=val.split("\n")
    #print "debug lines=%s"%lines
	
    ca=lines[1]
    dn=lines[2]
    ca=ca.replace(' issuer= ','')
    dn=dn.replace(' subject= ','')
    robot="OU=Robots/CN="+host_str+"/CN=cron"
    new_dn = dn.replace('OU=People',robot)

    
    return (new_dn,dn,ca)

def request_robot_cert():
    
    _debug_ = False
    allowed_hosts = ['gpsn01.fnal.gov','if01.fnal.gov','minos25.fnal.gov']
    for arg in sys.argv:
        if arg == '-d':
            _debug_ = True

    port="8443"
    vomrs="vomrs.fnal.gov"
    vo = "vomrs/vo-fermilab"
    if _debug_ :
        vo = "vomrs/fermilab"
        vomrs="fg0x5.fnal.gov"
    prefix=""
    (retVal,host)=commands.getstatusoutput("uname -n")
    home=os.environ.get("HOME")
    from_addr=os.environ.get("USER")
    from_addr+="@fnal.gov"
    if(host.find(".fnal.gov")<=0):
        host=host+".fnal.gov"
    if host not in allowed_hosts:
	print "you are trying to create a cert for %s" % host
	print "this script only works on the following: %s" % allowed_hosts
	print "please log on to one of these machines that "
	print "you intend to submit to the grid through and rerun this script"
	sys.exit(-1)

    (retVal,val)=commands.getstatusoutput("kx509")
    if(retVal):
        print """
        kx509 returned error: %s
        Your kerberos principal may have expired.
        Please kinit and try again""" % retVal
        sys.exit(-1)


    (new_dn,dn,ca) = make_new_dn(host)
    cmd = "voms-proxy-init -noregen -voms fermilab:/fermilab"
    if _debug_:
        print "executing %s" % cmd
        
    (retVal,val)=commands.getstatusoutput(cmd)
    if retVal:
        print "Warning voms-proxy-init returned the following information:"
        print val
        print "This may or may not be a problem, contact dbox@fnal.gov "
        print "with this output if it looks like an error message"


    while True:

# Added VO and MARS request 6-15-2011 J Urish
# Include answers in print statement.   
        voname=raw_input("Pleare enter VO/group (experiment) you are requesting robot cert for:")

	if voname == "lbne":
            print "lbne users should longer use this script. Please go to "
	    print "https://voms.fnal.gov:8443/voms/lbne/home/login.action " 
            print "and follow the instructions on that page"
            sys.exit(0)
        marsoft=raw_input("Do you wish to use the MARS software? [y/n]:")

        if voname == "lbne" and marsoft == "n":
            vo="vomrs/lbne"

        print """
        This script will attempt to register robot cert
        %s
        with vomrs server for  %s
        when this registration is approved, you will be able to
        submit to the grid from host %s
        Requested VO Group is: %s
        MARS software needed: %s
        
        possible user actions:
        
        [p]roceed with registration for submission from %s
        [c]hange host, I want to submit from a different machine
        [q]uit, get me out of here!
    
        """ % (new_dn, vo,host,voname,marsoft,host)
        resp=raw_input("please enter [p/c/q]:")
    
        if (resp[0]=='q'):
            sys.exit(0)
        if (resp[0]=='c'):
            host=raw_input("enter new submission host:")
            (new_dn,dn,ca) = make_new_dn(host)
        if (resp[0]=='p'):
            break;


    
        
    has_home_globus = False
    home_globus = home + "/.globus"
    if os.path.isdir(home_globus):
        has_home_globus = True
    if has_home_globus:
        print "HOME/.globus detected"
    passphrase = "S00per_Sekure"
    cmd = "echo %s | get-cert.sh" % passphrase
    if _debug_:
        print "executing %s" % cmd
        
    (retVal,val)=commands.getstatusoutput(cmd)
    lines=val.split("\n")
    p12='snake eyes'
    search_pat = "PKCS12 format"
    for x in lines:
	if _debug_ :
		print "searching '%s' for '%s' " % (x,search_pat)
        if(x.find(search_pat)==0):
            parts=x.split(": ")
            p12 = parts[1]
##    print "p12 is ",p12
##    print "bailing.."
##    sys.exit(0)

    if p12 == 'snake eyes':
        print "error with get-cert.sh, exiting!"
        sys.exit(0);

    cmd = "openssl pkcs12 -in %s -out %s/client.pem -clcerts -nokeys" % (p12,home)

    if _debug_:
        print "executing %s" % cmd
    child = pexpect.spawn (cmd)
    child.expect('Enter Import Password')
    child.sendline()
    cmd = "openssl pkcs12 -in %s -out %s/key.pem -nocerts" % (p12,home)

    if _debug_:
        print "\n\nexecuting %s" % cmd

    child2 = pexpect.spawn (cmd)
    child2.expect('Enter Import Password')
    child2.sendline()
    child2.expect('Enter PEM pass phrase')
    child2.sendline(passphrase)
    child2.expect('Enter PEM pass phrase')
    child2.sendline(passphrase)

    dn=webalyze(dn)
    ca=webalyze(ca)
    new_dn_copy=new_dn
    new_dn=webalyze(new_dn)


    cmd0="""curl -c %s/cookie.txt  -o %s/vomrs_search.html -E %s/client.pem:%s --key %s/key.pem -k -d 'SearchCriteria_DN=%s&SearchCriteria_CA=%s&SearchCriteria_First+name=&SearchCriteria_Last+name=&SearchCriteria_Phone=&SearchCriteria_STATUS=&SearchCriteria_ROLE=&SearchCriteria_RIGHTS=&SearchCriteria_REPDN=&SearchCriteria_REPCA=&SearchCriteria_CERT_STATUS=&HeaderSelection_PRIMARY=Y&HeaderSelection_STATUS=Y&HeaderSelection_LINES_NUM=100&Submit=Search&SearchCriteria_INSTITUTION=Fermilab' 'https://%s:%s/%s/vomrs?path=/RootNode/MemberAction/SetNotify&action=execute&do=select'""" % (home,home,home,passphrase,home,dn,ca,vomrs,port,vo)
    
##    print "curl cmd is %s" % cmd    
##    print "bailing.."
##    sys.exit(0)

    
    if _debug_:
        print "\n\nexecuting %s \n\n" % cmd0

    
# Changed variable from_addr to user_addr to fix bug with email address 6-21-2011 J. Urish
    (retVal,host)=commands.getstatusoutput(cmd0)
    user_addr=os.environ.get("USER")
    user_addr=user_addr+"%40fnal.gov"

# Changed variable from_addr to user_addr to fix bug with email address 6-21-2011 J. Urish
    cmd1="""curl -b %s/cookie.txt  -o %s/vomrs_result.html -E %s/client.pem:%s --key %s/key.pem -k -d 'SelectedResults_EMAIL_0=%s&Submit=Submit' 'https://%s:%s/%s/vomrs?path=/RootNode/MemberAction/SetNotify&action=execute&do=doAction'""" % (home,home,home,passphrase,home,user_addr,vomrs,port,vo)

    if _debug_:
        print "\n\nexecuting %s " % cmd1

    #print "curl cmd is %s" % cmd2
    (retVal,host)=commands.getstatusoutput(cmd1)







    

    cmd="""curl -c %s/cookie.txt  -o %s/vomrs_search.html -E %s/client.pem:%s --key %s/key.pem -k -d 'SearchCriteria_DN=%s&SearchCriteria_CA=%s&SearchCriteria_First+name=&SearchCriteria_Last+name=&SearchCriteria_Phone=&SearchCriteria_STATUS=&SearchCriteria_ROLE=&SearchCriteria_RIGHTS=&SearchCriteria_REPDN=&SearchCriteria_REPCA=&SearchCriteria_CERT_STATUS=&HeaderSelection_PRIMARY=Y&HeaderSelection_STATUS=Y&HeaderSelection_LINES_NUM=100&Submit=Search&SearchCriteria_INSTITUTION=Fermilab' 'https://%s:%s/%s/vomrs?path=/RootNode/MemberAction/MemberDNs/AddDN&action=execute&do=select'""" % (home,home,home,passphrase,home,dn,ca,vomrs,port,vo)
    
##    print "curl cmd is %s" % cmd    
##    print "bailing.."
##    sys.exit(0)

    
    if _debug_:
        print "\n\nexecuting %s \n\n" % cmd

    
    (retVal,host)=commands.getstatusoutput(cmd)


    cmd2="""curl -b %s/cookie.txt  -o %s/vomrs_result.html -E %s/client.pem:%s --key %s/key.pem -k -d 'SelectedResults_NEWDN_0=%s&SelectedResults_NEWCA_0=%s&SelectedResults_REASON_0=condor+glidein&Submit=Submit' 'https://%s:%s/%s/vomrs?path=/RootNode/MemberAction/MemberDNs/AddDN&action=execute&do=doAction'""" % (home,home,home,passphrase,home,new_dn,ca,vomrs,port,vo)

    if _debug_:
        print "\n\nexecuting %s " % cmd2

    #print "curl cmd is %s" % cmd2
    (retVal,host)=commands.getstatusoutput(cmd2)

    check_cmd = "grep 'You have successfully added certificate' %s/vomrs_result.html" % home

    (retVal,host)=commands.getstatusoutput(check_cmd)
    if retVal==0 :
        print "Request submitted successfully.  You will receive mail "
        print "when a Grid Admin approves your request so you can submit"
        print "to the grid"
    else:
        check_cmd = "grep 'already exists in VO database' %s/vomrs_result.html" % home

        (retVal,host)=commands.getstatusoutput(check_cmd)
        if retVal==0 :
            print "Request unsuccessful, you (or someone) has already"
            print "requested this certificate.  You will receive mail "
            print "when a Grid Admin approves your request so you can submit"
            print "to the grid"
        else:
            print "unknown error processing request"
            print "please contact a grid admin.  Attach file "
            print "%s/vomrs_result.html to your message " % home

# Changed "to" to a list to allow multiple recipients 6-20-2011 J. Urish
    to=["ifront-computing@fnal.gov"]
    if new_dn.find("if01")>0:
        to=["minerva-computing@fnal.gov"]
    if new_dn.find("if05")>0:
        to=["nova-computing@fnal.gov"]
    if new_dn.find("minos25")>0:
        to=["minos-data@fnal.gov"]
# Added following test. Send mail to Nikholi Mokhov if there is a MARS software request. 6-15-2011 J. Urish
    if marsoft == "y":
        to+=["mokhov@fnal.gov"]
    
# Added VO group name to message 6-15-2011 J. Urish
    msg = MIMEText("robot cert %s was just requested for the %s VO/group.\n Please make sure they are approved as members of the appropriate group in vomrs" % (new_dn_copy,voname))
    msg['Subject']="User %s requested robot cert for %s VO/group " % (from_addr,voname)
    msg['From']=from_addr
# Added join to express multiple recipients in email "To" line 6-20-2011 J. Urish
    msg['To']=', '.join(to)
    s = smtplib.SMTP()
    s.connect()
    s.sendmail(from_addr,to,msg.as_string())
    s.close()
            
    sys.exit(retVal)

    
if __name__ == '__main__':
	request_robot_cert()
