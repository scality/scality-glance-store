#!/bin/bash -xue

TEMPEST_DIR=/opt/stack/tempest
sudo pip install -r $TEMPEST_DIR/test-requirements.txt -r $TEMPEST_DIR/requirements.txt 
sudo pip install --upgrade nose
set +e
nosetests -w $TEMPEST_DIR/tempest/api/image --exe --with-xunit --xunit-file=${WORKSPACE}/nosetests.xml
set -e
echo "Entering WORKSPACE."
cd $WORKSPACE
mkdir jenkins-logs
echo "Creating jenkins-log directory."
cp -R /opt/stack/logs/* jenkins-logs/
sudo chown jenkins jenkins-logs/*
exit 0
