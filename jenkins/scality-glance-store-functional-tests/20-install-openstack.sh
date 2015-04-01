#!/bin/bash -xue

function common {
    source jenkins/openstack-ci-scripts/jenkins/distro-utils.sh

    if is_centos; then
        sudo yum install -y wget
    fi

    if [[ $os_CODENAME == "precise" ]]; then
        sudo add-apt-repository --yes cloud-archive:icehouse
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
