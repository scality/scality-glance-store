#!/bin/bash -xue

cd /opt/stack/tempest

echo "*** Hack: Apply https://review.openstack.org/#/c/226375/"
curl "https://review.openstack.org/gitweb?p=openstack/tempest.git;a=patch;h=edee6507df2b73ec76cccc37317581b1741fda2d" | git am

git log -n2

set +e
tox -e all -- tempest.api.image
RC=$?
testr last --subunit > $WORKSPACE/testrepository.subunit
set -e

echo "Entering WORKSPACE."
cd $WORKSPACE
mkdir jenkins-logs
echo "Creating jenkins-log directory."
cp -R /opt/stack/logs/* jenkins-logs/
sudo chown jenkins jenkins-logs/*

# Create a test result report
sudo pip install junitxml
cat ${WORKSPACE}/testrepository.subunit | subunit2junitxml -o ${WORKSPACE}/nosetests.xml

exit $RC
