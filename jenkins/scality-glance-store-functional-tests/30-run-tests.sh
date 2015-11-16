#!/bin/bash -xue

cd /opt/stack/tempest

echo "*** Hack: Apply https://review.openstack.org/#/c/226375/"
curl "https://review.openstack.org/gitweb?p=openstack/tempest.git;a=patch;h=edee6507df2b73ec76cccc37317581b1741fda2d" | git am

git log -n2

set +e
tox -e all -- tempest.api.image
RC=$?
set -e

sudo pip install junitxml
# Create a test result report
testr last --subunit | subunit2junitxml -o ${WORKSPACE}/nosetests.xml

exit $RC
