#!/bin/bash -xue

function is_centos {
    [[ -f /etc/centos-release ]]
}

function is_deb {
    [[ -f /etc/debian_version ]]
}

function common {
    wget https://bootstrap.pypa.io/ez_setup.py -O - | sudo python -
    sudo easy_install pip

    if is_centos; then
        sudo pip install -U six
    fi

    git clone -b ${DEVSTACK_BRANCH:-master} https://github.com/openstack-dev/devstack.git
    cp devstack/samples/local.conf devstack/local.conf
    cat >> devstack/local.conf <<EOF
disable_service n-xvnc n-novnc n-obj n-cauth h-eng h-api h-api-cfn h-api-cw horizon
SCREEN_LOGDIR="\${DEST}/logs"
EOF
    cp jenkins/${JOB_NAME%%/*}/extras.d/55-scality-glance-store.sh devstack/extras.d/55-scality-glance-store.sh
    FORCE=yes ./devstack/stack.sh
}

common
