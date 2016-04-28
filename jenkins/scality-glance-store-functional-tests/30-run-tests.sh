#!/bin/bash -xue

cd /opt/stack/tempest
set +e
tox -e all -- tempest.api.image
RC=$?
set -e

sudo pip install junitxml
# Create a test result report
testr last --subunit | subunit2junitxml -o ${WORKSPACE}/nosetests.xml

exit $RC
