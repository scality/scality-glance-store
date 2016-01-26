#!/bin/bash -xue

echo "Entering WORKSPACE."
cd $WORKSPACE

echo "Creating jenkins-log directory."
mkdir jenkins-logs
cp -R /opt/stack/logs/* jenkins-logs/

if [[ -f "/var/log/messages" ]]; then
    sudo cp /var/log/messages jenkins-logs/messages
fi

if [[ -f "/var/log/syslog" ]]; then
    sudo cp /var/log/syslog jenkins-logs/syslog
fi

# || true has been added to workaround this failure:
# "chown fails with chown: cannot dereference ‘jenkins-logs/xx’:
# No such file or directory"
sudo chown jenkins jenkins-logs/* || true
