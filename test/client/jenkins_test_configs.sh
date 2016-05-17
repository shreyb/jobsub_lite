source /fnal/ups/etc/setups.sh
setup cigetcert
setup kx509
unset X509_USER_CERT
unset X509_USER_KEY
export X509_USER_PROXY=/tmp/x509up_u${UID}
export KRB5CCNAME=`ls -lart /tmp/krb5cc_${UID}* | tail -1 | awk '{print $9}'`
kx509
export X509_USER_CERT=/tmp/x509up_u${UID}
export X509_USER_KEY=/tmp/x509up_u${UID}
unset X509_USER_PROXY
