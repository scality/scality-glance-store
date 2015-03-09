#!/bin/bash -xue

function common {
    git clone https://github.com/openstack-dev/devstack.git
    cp devstack/samples/local.conf devstack/local.conf
    cat >> devstack/local.conf <<EOF
disable_service n-xvnc n-novnc n-obj n-cauth h-eng h-api h-api-cfn h-api-cw horizon
SCREEN_LOGDIR="\${DEST}/logs"
EOF
    cp jenkins/${JOB_NAME%%/*}/extras.d/55-scality-glance-store.sh devstack/extras.d/55-scality-glance-store.sh
    ./devstack/stack.sh
}

common
