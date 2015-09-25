#!/bin/bash -xue

function common {
    source jenkins/openstack-ci-scripts/jenkins/distro-utils.sh

    if is_centos; then
        sudo yum install -y wget
    fi

    if [[ $os_CODENAME == "precise" ]]; then
        sudo add-apt-repository --yes cloud-archive:icehouse
    fi

    wget https://bootstrap.pypa.io/get-pip.py -O - | sudo python -
    sudo pip install -U six

    if is_centos; then
        sudo yum install -y ftp://ftp.is.co.za/mirror/fedora.redhat.com/epel/6/x86_64/python-mox-0.5.3-2.el6.noarch.rpm

        if test "${DEVSTACK_BRANCH:-x}" = "stable/juno"; then
            RHEL6_RDO_REPO_RPM="http://buildlogs.centos.org/centos/6/cloud/x86_64/openstack-juno/centos-release-openstack-juno-2.el6.noarch.rpm"
            export RHEL6_RDO_REPO_RPM
            RHEL6_RDO_REPO_ID="CentOS-OpenStack-juno"
            export RHEL6_RDO_REPO_ID
        fi
    fi

    git clone -b ${DEVSTACK_BRANCH:-master} https://github.com/openstack-dev/devstack.git
    cp devstack/samples/local.conf devstack/local.conf
    cat >> devstack/local.conf <<EOF
disable_service n-xvnc n-novnc n-obj n-cauth h-eng h-api h-api-cfn h-api-cw horizon
SCREEN_LOGDIR="\${DEST}/logs"
EOF
    cp jenkins/${JOB_NAME%%/*}/extras.d/55-scality-glance-store.sh devstack/extras.d/55-scality-glance-store.sh

    ./devstack/stack.sh
}

common
