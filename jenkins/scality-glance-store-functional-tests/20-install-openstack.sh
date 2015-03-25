#!/bin/bash -xue

function is_centos {
    [[ -f /etc/centos-release ]]
}

function is_deb {
    [[ -f /etc/debian_version ]]
}

function common {
    if is_centos; then
        sudo yum install -y wget
    fi

    wget https://bootstrap.pypa.io/ez_setup.py -O - | sudo python -
    sudo easy_install pip
    sudo easy_install -U six

    if is_centos; then
        sudo yum install -y https://kojipkgs.fedoraproject.org//packages/python-mox/0.5.3/2.el6/noarch/python-mox-0.5.3-2.el6.noarch.rpm
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
