#!/usr/bin/env python
import unittest2 as unittest
import authutils
import os
import hashlib
import logger

"""Unit test for jobsub/server/webapp/authutils.py functions
   TODO: These tests are very dependent on the contents of jobsub.ini
   and should not use the default one stored on the server, it can change
"""

class authutil_tests(unittest.TestCase):

    def setUp(self):
        self.existProxyFile = authutils.mk_temp_fname('/tmp/unit_test_proxy')
        self.noExistFile = '/tmp/does/not/exist/nope/no/sir'

    def tearDown(self):
        if os.path.exists(self.existProxyFile):
            os.remove(self.existProxyFile)

    def test_get_voms(self):
        grp = 'nova'
        v = authutils.get_voms(grp)
        self.assertEqual(v,'fermilab:/fermilab/%s'%grp)

        grp = 'marsmu2e'
        v = authutils.get_voms(grp)
        self.assertEqual(v,'fermilab:/fermilab/mars/mu2e')

        with self.assertRaises(authutils.AcctGroupNotConfiguredError):
            grp = 'noGroupHerePeopleMoveAlong'
            v = authutils.get_voms(grp)
            self.assertIsNone(v)

    def test_get_voms_attrs(self):
        grp = 'nova'
        v = authutils.get_voms_attrs(grp,'Production')
        self.assertEqual(v,'fermilab:/fermilab/%s/Role=Production'%grp)

        grp = 'marsmu2e'
        v = authutils.get_voms_attrs(grp,'Production')
        self.assertEqual(v,'fermilab:/fermilab/mars/mu2e/Role=Production')

    def test_krbrefresh_query_fmt(self):
        s = authutils.krbrefresh_query_fmt()
        self.assertIsInstance(s, str)

    def test_krb5cc_to_x509(self):
        test_fname = self.existProxyFile
        krb=os.environ.get('KRB5CCNAME')
        if krb and os.path.exists(krb):
            authutils.krb5cc_to_x509(krb,test_fname)
            self.assertTrue('created %s' % test_fname)

    def test_x509pair_to_vomsproxy(self):
        test_fname = self.existProxyFile
        krb=os.environ.get('KRB5CCNAME')
        if krb and os.path.exists(krb):
            authutils.krb5cc_to_x509(krb,test_fname)
            authutils.x509pair_to_vomsproxy(test_fname,test_fname,test_fname,'nova','Production')
            self.assertTrue('created %s' % test_fname)

    def test_krb5cc_to_vomsproxy(self):
        test_fname = self.existProxyFile
        krb=os.environ.get('KRB5CCNAME')
        if krb and os.path.exists(krb):
            authutils.krb5cc_to_vomsproxy(krb,test_fname,'nova','Production')
            self.assertTrue('created %s' % test_fname)

    def test_krb5cc_to_x509_failure(self):
        with self.assertRaises(authutils.OtherAuthError):
            krb = self.noExistFile
            test_fname = self.existProxyFile
            authutils.krb5cc_to_x509(krb,test_fname)

    def test_clean_proxy_dn(self):
        dn1 = '/DC=org/DC=cilogon/C=US/O=Fermi National Accelerator Laboratory/OU=People/CN=Dennis Box/CN=UID:dbox'
        dn2 = '/DC=org/DC=cilogon/C=US/O=Fermi National Accelerator Laboratory/OU=People/CN=Dennis Box/CN=UID:dbox/CN=862097073'
        dn3 = '/DC=org/DC=cilogon/C=US/O=Fermi National Accelerator Laboratory/OU=People/CN=Dennis Box/CN=UID:dbox/CN=862097073/CN=1402249658'
        self.assertEqual(dn1,authutils.clean_proxy_dn(dn1))
        self.assertEqual(dn1,authutils.clean_proxy_dn(dn2))
        self.assertEqual(dn1,authutils.clean_proxy_dn(dn3))


    def test_x509_proxy_fname(self):
        name = 'dbox'
        grp = 'nova'
        fname = authutils.x509_proxy_fname(name,grp)
        #/var/lib/jobsub/creds/proxies/nova/x509cc_dbox
        self.assertEqual(fname, '/var/lib/jobsub/creds/proxies/%s/x509cc_%s'%(grp,name))
        
        name='novapro'
        role='Production'
        dn='/DC=org/DC=cilogon/C=US/O=Fermi National Accelerator Laboratory/OU=People/CN=Dennis Box/CN=UID:dbox'
        dig = hashlib.sha1()
        dig.update(dn)
        tgt_name = '/var/lib/jobsub/creds/proxies/%s/x509cc_%s_%s_%s'%(grp,name,role,dig.hexdigest())

        fname = authutils.x509_proxy_fname(name,grp,role,dn)
        self.assertEqual(fname, tgt_name)
        
        dn = '/DC=org/DC=cilogon/C=US/O=Fermi National Accelerator Laboratory/OU=People/CN=Dennis Box/CN=UID:dbox/CN=862097073'
        fname = authutils.x509_proxy_fname(name,grp,role,dn)
        self.assertEqual(fname, tgt_name)

        dn = '/DC=org/DC=cilogon/C=US/O=Fermi National Accelerator Laboratory/OU=People/CN=Dennis Box/CN=UID:dbox/CN=862097073/CN=1402249658'
        fname = authutils.x509_proxy_fname(name,grp,role,dn)
        self.assertEqual(fname, tgt_name)

    def test_is_valid_cache_doesnt_exist(self):
        badfile=self.noExistFile
        nf = authutils.is_valid_cache(badfile)
        self.assertEqual(nf,False)

    def test_is_valid_cache_exists(self):
        ld=os.environ.get('KRB5CCNAME')
        if ld and os.path.exists(ld):
            nf = authutils.is_valid_cache(ld)
            self.assertEqual(nf,True)
        else:
            return True

    def test_needs_refresh_doesnt_exist(self):
        badfile=self.noExistFile
        nf = authutils.needs_refresh(badfile)
        self.assertEqual(nf,True)

    def test_needs_refresh_exists(self):
        goodfile = self.existProxyFile
        nf = authutils.needs_refresh(goodfile)
        self.assertEqual(nf,False)

if __name__ == '__main__':
        #unittest.main(buffer=True)
        suite = unittest.TestLoader().loadTestsFromTestCase(authutil_tests)
        unittest.TextTestRunner(verbosity=1).run(suite)
