#!/bin/bash -xue

source jenkins/openstack-ci-scripts/jenkins/distro-utils.sh

if is_centos; then
    sudo yum install -y ftp://ftp.is.co.za/mirror/fedora.redhat.com/epel/6/x86_64/python-mox-0.5.3-2.el6.noarch.rpm

    if test "${DEVSTACK_BRANCH:-x}" = "stable/juno"; then
        export RHEL6_RDO_REPO_RPM="http://buildlogs.centos.org/centos/6/cloud/x86_64/openstack-juno/centos-release-openstack-juno-2.el6.noarch.rpm"
        export RHEL6_RDO_REPO_ID="CentOS-OpenStack-juno"
    fi
fi

if [[ $os_CODENAME == "precise" ]]; then
    sudo add-apt-repository --yes cloud-archive:icehouse
fi

git clone -b ${DEVSTACK_BRANCH:-master} https://github.com/openstack-dev/devstack.git
cat > devstack/local.conf <<-EOF
	[[local|localrc]]
	DATABASE_PASSWORD=testtest; RABBIT_PASSWORD=testtest; SERVICE_TOKEN=testtest; SERVICE_PASSWORD=testtest; ADMIN_PASSWORD=testtest; SCREEN_LOGDIR=\${DEST}/logs
	disable_service n-xvnc n-novnc n-obj h-eng h-api h-api-cfn h-api-cw horizon
	[[post-config|\$GLANCE_API_CONF]]
	[glance_store]
	default_store = scality
	stores = glance.store.filesystem.Store,glance.store.http.Store,glance.store.scality.Store
	scality_sproxyd_endpoints = http://127.0.0.1:81/proxy/bpchord
EOF

cat > devstack/extras.d/55-scality-glance-store.sh <<-EOF
	if is_service_enabled g-api; then
	    if [[ "\$1" == "stack" && "\$2" == "install" ]]; then
	        sudo pip install https://github.com/scality/scality-sproxyd-client/archive/master.tar.gz
	        sudo pip install .
	    fi
	fi
EOF

./devstack/stack.sh
