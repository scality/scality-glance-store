#!/bin/bash -xue

cd /opt/stack/tempest

echo "*** Hack: Apply https://review.openstack.org/#/c/252837/"
curl "https://review.openstack.org/gitweb?p=openstack/tempest.git;a=patch;h=660b440f12c607d720e59e1c6ab297c2c28b1ea3" | git am

git log -n2

set +e
tox -e all -- tempest.api.image
RC=$?
set -e

sudo pip install junitxml
# Create a test result report
testr last --subunit | subunit2junitxml -o ${WORKSPACE}/nosetests.xml

exit $RC
