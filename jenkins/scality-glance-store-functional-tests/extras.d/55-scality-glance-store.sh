# 55-scality-glance-store - Devstack extra script to configure Glance API with Scality store

function install_scality_store {
    sudo pip install https://github.com/scality/scality-sproxyd-client/archive/master.tar.gz
    # For some reason, doing this failed: glance-api would not restart,
    # complaining about an old version of python-six.
    # Probably a setuptools version issue
    #sudo python setup.py install
    sudo pip install .
}

function enable_scality_store {
    iniset $GLANCE_API_CONF DEFAULT default_store scality
    iniset $GLANCE_API_CONF glance_store default_store scality
    iniset $GLANCE_API_CONF glance_store stores "glance.store.filesystem.Store, glance.store.http.Store, glance.store.scality.Store"
    iniset $GLANCE_API_CONF glance_store scality_sproxyd_endpoints http://127.0.0.1:81/proxy/chord_path/
}

if is_service_enabled g-api; then
    if [[ "$1" == "stack" && "$2" == "install" ]]; then
        echo_summary "Post-config hook : install scality-glance-store."
        install_scality_store
    fi
    if [[ "$1" == "stack" && "$2" == "post-config" ]]; then
        echo_summary "Post-config hook : enable scality-glance-store."
        enable_scality_store
    fi
fi 
