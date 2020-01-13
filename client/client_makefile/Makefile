# Makefile that sets up a ups and spack directories
# intent is to make using spack and distribute using ups
# author Dennis Box, dbox@fnal.gov
#
PRODUCT_VERSION = v1_2
PRODUCT_NAME = python_future_six_request
SHELL := /bin/bash
UNAME_S := $(shell uname -s)
KERNEL_MAJOR := $(shell uname -r | sed -e 's/\..*//')
SPACK_HOME := $(shell ./spack_home)
PYFLAVOR  := $(shell ./pyflavor)
VENV_SRC_DIR=virtualenv-16.7.7
RVER=

ifeq ($(UNAME_S),Darwin)
	UPS_TARBALL = ups_bootstrap_traditional_v5_2_0_Darwin64bit+15.tar.gz
	UPS_URL = ftp://ftp.fnal.gov/products/bootstrap/v3_0/${UPS_TARBALL}
	UPS_DIR = mac_ups
endif
ifeq ($(UNAME_S),Linux)
	ifeq ($(KERNEL_MAJOR),3)
		UPS_TARBALL = ups_bootstrap_traditional_v5_1_7_Linux64bit+3.10-2.12.tar.gz
		UPS_URL = ftp://ftp.fnal.gov/products/bootstrap/v3_0/${UPS_TARBALL}
		UPS_DIR = sl7_ups
	endif
	ifeq ($(KERNEL_MAJOR),2)
		VENV_SRC_DIR=virtualenv-12.0.7
		UPS_TARBALL = ups_bootstrap_traditional_v5_2_0_Linux64bit+2.6-2.12.tar.gz
		UPS_URL = ftp://ftp.fnal.gov/products/bootstrap/v3_0/${UPS_TARBALL}
		UPS_DIR = sl6_ups
    ifeq (${PYFLAVOR},python2.6)
			RVER='==2.0.0'
    endif
	endif
endif
VENV_TARBALL=${VENV_SRC_DIR}.tar.gz
VENV_TARBALL_URL=https://pypi.python.org/packages/source/v/virtualenv/${VENV_TARBALL}
VENV_DEV_DIR=venv-${PYFLAVOR}
UPS_SCRIPT = ${UPS_DIR}/etc/setups.sh
UPS_SOURCEME = ups_sourceme.sh
SPACK_REPO = github.com/spack/spack.git
SPACK_SOURCEME = spack_sourceme.sh

.PHONY: all clean really_clean  report pycurl future_six_request ups_product_dir the_rest

#all:  ${UPS_DIR}  ${UPS_SOURCEME} ${SPACK_SOURCEME} ${SPACK_HOME} ${VENV_DEV_DIR} ups_curl
all:  ${UPS_DIR}  ${UPS_SOURCEME}  ${VENV_DEV_DIR} ups_curl

${VENV_DEV_DIR}: ${VENV_SRC_DIR}
	python ${VENV_SRC_DIR}/virtualenv.py ${VENV_DEV_DIR}


${VENV_SRC_DIR}:
	@echo making ${VENV_SRC_DIR}
	@wget ${VENV_TARBALL_URL}
	@tar xvzf ${VENV_TARBALL}
	@rm -rf ${VENV_TARBALL}



${UPS_DIR}:
	@echo making ${UPS_DIR}
	@wget ${UPS_URL}
	@mkdir -p ${UPS_DIR}
	@cd ${UPS_DIR} && tar xzf ../${UPS_TARBALL} && cd ..
	@rm -rf ${UPS_TARBALL}

ups_curl: ${UPS_DIR}
	$(shell source ${UPS_SOURCEME} && upd install curl v7_67_0 && ups declare -c curl v7_67_0)

${UPS_SOURCEME}:
	@echo 'KERNEL_MAJOR=`uname -r | sed -e "s/\..*//"`' > ${UPS_SOURCEME}
	@echo 'UNAME_S=`uname -s`' >> ${UPS_SOURCEME}
	@echo 'test "$${UNAME_S}" = "Darwin" && . mac_ups/etc/setups.sh'  >> ${UPS_SOURCEME}
	@echo 'test "$${UNAME_S}" = "Linux" && test "$${KERNEL_MAJOR}" = "3" && . sl7_ups/etc/setups.sh'  >> ${UPS_SOURCEME}
	@echo 'test "$${UNAME_S}" = "Linux" && test "$${KERNEL_MAJOR}" = "2" && . sl6_ups/etc/setups.sh'  >> ${UPS_SOURCEME}
	@echo 'setup ups && setup upd'  >> ${UPS_SOURCEME}
  @echo 'export PRODUCTS=$${PRODUCTS}:/cvmfs/larsoft.opensciencegrid.org/products' >> ${UPS_SOURCEME}

${SPACK_HOME}:
	@if [  -d $${SPACK_HOME} ]; then \
		echo $${SPACK_HOME} already exists; \
	else \
	    cd $(shell dirname ${SPACK_HOME}) &&\
	   	git clone https://github.com/spack/spack.git ; \
	fi
	. ${SPACK_SOURCEME} && spack install lmod

${SPACK_SOURCEME}:
	@echo 'source  $${SPACK_HOME}/share/spack/setup-env.sh' > ${SPACK_SOURCEME}
	@echo 'export SPACK_LMOD=`spack location -i lmod`' >> ${SPACK_SOURCEME}
	@echo 'test -e "$${SPACK_LMOD}/lmod" && source "$${SPACK_LMOD}/lmod/lmod/init/bash"' >> ${SPACK_SOURCEME}

setup_spack: ${SPACK_HOME}
	. ${SPACK_SOURCEME}

pycurl:
	@echo "installing pycurl"
	@touch ${PYFLAVOR}.log
	@echo '============================================================' >> ${PYFLAVOR}.log
	@echo $(shell date >> ${PYFLAVOR}.log)
	@echo $(shell (source ups_sourceme.sh && setup curl && source ${VENV_DEV_DIR}/bin/activate &&  easy_install pycurl)  >> ${PYFLAVOR}.log 2>&1 || true)
	@echo $(shell ./fix_pycurl_egg ${VENV_DEV_DIR} >> ${PYFLAVOR}.log 2>&1 || true)

future_six_request: pycurl
	@echo "installing future six requests"
	@touch ${PYFLAVOR}.log
	@echo '============================================================' >> ${PYFLAVOR}.log
	@echo $(shell date >> ${PYFLAVOR}.log)
	@echo $(shell (source ups_sourceme.sh && setup curl && source ${VENV_DEV_DIR}/bin/activate && pip install requests${RVER}  && pip install future && pip install six) >>${PYFLAVOR}.log 2>&1  || true )
	$(shell for D in `find ${VENV_DEV_DIR}/lib -type d`; do chmod a+x $$D; done)
	@chmod -R a+r ${VENV_DEV_DIR}/lib
	@chmod -R g+w ${VENV_DEV_DIR}/lib

ups_product_dir: future_six_request
	mkdir -p $(shell echo $${PRODUCTS} | sed -e 's/:.*//' )/${PRODUCT_NAME}/${PRODUCT_VERSION}.version
	mkdir -p $(shell echo $${PRODUCTS} | sed -e 's/:.*//' )/../prd/${PRODUCT_NAME}/${PRODUCT_VERSION}/$(shell ups flavor)-${PYFLAVOR}
	@echo '======${PRODUCT_NAME}/${PRODUCT_VERSION}==============================================' >> ${PYFLAVOR}.log
	@echo $(shell date >> ${PYFLAVOR}.log)
	$(shell ./populate_ups ${PRODUCT_NAME} ${PRODUCT_VERSION} ${PYFLAVOR} >> ${PYFLAVOR}.log 2>&1 )
	$(shell ./make_tablefile.py ${PRODUCT_NAME} ${PRODUCT_VERSION} ${PYFLAVOR} >> ${PYFLAVOR}.log 2>&1 )


the_rest: ups_product_dir


report:
	@echo  $(shell source ${SPACK_SOURCEME} && source ${UPS_SOURCEME} && ups list -aK+ && spack load curl && curl --version | tr '(' ' '| tr ')' ' ')

tidy:
	@rm  -f *.gz

clean: tidy
	@rm -rf  ${UPS_DIR} ${UPS_SOURCEME} ${SPACK_SOURCEME} ${VENV_SRC_DIR} venv-python* *log

really_clean: clean
	rm -rf spack
