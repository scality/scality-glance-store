Scality Object Storage backend for OpenStack Glance
===================================================
This package implements a back-end for OpenStack_ Glance_ storing objects in a
Scality_ RING installation. It is compatible with Openstack Juno **and** Kilo.

.. _OpenStack: http://openstack.org
.. _Glance: http://docs.openstack.org/developer/glance/
.. _Scality: http://scality.com

Installation
------------
This package depends on `Scality Sproxyd client`_, a Python client library for Scality Sproxyd connector. It must 
be installed before installing this package.

.. _Scality Sproxyd client: https://github.com/scality/scality-sproxyd-client

1. Install this package:

   .. code-block:: console

       python setup.py install

2. Configure Glance API. Edit your *glance-api.conf* file to add the Scality backend to the list of known
   Glance stores:

   .. code-block:: ini

    [glance_store]
    stores = glance.store.filesystem.Store,
             glance.store.scality.Store,
             glance.store.http.Store
   **N.B** This is a configuration example. Just make sure *glance.store.scality.Store* appears in the list
   of *stores* in the *[glance_store]* section of *glance-api.conf*.

3. Configure the Sproxyd connectors to use. Edit *glance-api.conf* and add the list of your Sproxyd connectors
   configured to accept **query by path** in the *[glance_store]* section:

   .. code-block:: ini

    [glance_store]
    scality_sproxyd_endpoints = http://4.5.9.2:81/proxy/chord_path/,http://4.5.9.4:81/proxy/arc_path/

4. (optional) Use the Scality Store as the default image store. Newly uploaded Glance image will be stored in
   Scality Ring. As of OpenStack Kilo, the default store has to be set in both the *DEFAULT*
   section and the *glance_store* section (for compatibility reasons) of *glance-api.conf*.
   
   .. code-block:: ini
   
    [DEFAULT]
    default_store = scality
    [glance_store]
    default_store = scality
  
5. Restart the OpenStack Glance API system service. 
