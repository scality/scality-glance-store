#!/bin/bash -xue

TEMPEST_DIR=/opt/stack/tempest

virtualenv venv_for_nosetests
set +o nounset # See https://github.com/pypa/virtualenv/issues/150
source venv_for_nosetests/bin/activate
set -o nounset

pip install -r $TEMPEST_DIR/test-requirements.txt -r $TEMPEST_DIR/requirements.txt nose

set +e
nosetests -w $TEMPEST_DIR/tempest/api/image --exe --with-xunit --xunit-file=${WORKSPACE}/nosetests.xml
set -e

set +o nounset # See https://github.com/pypa/virtualenv/issues/150
deactivate
set -o nounset

echo "Entering WORKSPACE."
cd $WORKSPACE
mkdir jenkins-logs
echo "Creating jenkins-log directory."
cp -R /opt/stack/logs/* jenkins-logs/
sudo chown jenkins jenkins-logs/*
exit 0
