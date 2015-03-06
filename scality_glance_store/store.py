# Copyright (c) 2015 Scality
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import hashlib
import logging

from glance_store import backend
from glance_store import capabilities
from glance_store.common import utils
from glance_store import driver
from glance_store import exceptions
from glance_store.i18n import _, _LI, _LE
from glance_store import location

from oslo_config import cfg
from oslo_utils import excutils
from oslo_utils import units

import scality_sproxyd_client.exceptions
from scality_sproxyd_client import sproxyd_client
import scality_sproxyd_client.utils


LOG = logging.getLogger(__name__)
logging.getLogger('urllib3.util.retry').level = logging.INFO

"""
rule="OUTPUT -p tcp --dport 81 -d 167.88.149.214 -j DROP";
sudo iptables --check $rule &> /dev/null || sudo iptables -A $rule
sudo iptables -D $rule
"""

_SPROXYD_OPTS = [
    cfg.ListOpt('scality_sproxyd_endpoints',
                help=_("Comma-separated list of Sproxyd endpoints which "
                       "accept queries 'by path' (e.g. 'http://10.5.9.2:81/"
                       "proxy/chord_path/')")),
]


class StoreLocation(location.StoreLocation):
    """
    Class describing a relative Sproxyd URI.

    In the form of: scality://image
    """

    def process_specs(self):
        self.image_id = self.specs['image_id']

    def get_uri(self):
        return "scality://%s" % self.image_id

    def parse_uri(self, uri):
        prefix = 'scality://'
        pieces = uri[len(prefix):].split('/')
        if not uri.startswith(prefix) or len(pieces) > 1 or not pieces[0]:
            msg = _('Invalid URI : %s. URI must be of the form '
                    'scality://image') % uri
            LOG.info(msg)
            raise exceptions.BadStoreUri(message=msg)

        self.image_id = pieces[0]


class Store(driver.Store):

    _CAPABILITIES = (capabilities.BitMasks.RW_ACCESS |
                     capabilities.BitMasks.DRIVER_REUSABLE)
    CHUNKSIZE = 64 * units.Ki
    OPTIONS = _SPROXYD_OPTS

    def __init__(self, conf):
        super(Store, self).__init__(conf)

        endpoints = self.conf.glance_store.scality_sproxyd_endpoints
        self.sproxyd_client = sproxyd_client.SproxydClient(endpoints)

    @staticmethod
    def get_schemes():
        return ('scality',)

    @capabilities.check
    def get(self, location, offset=0, chunk_size=None, context=None):
        """
        Takes a `glance_store.location.Location` object that indicates
        where to find the image file, and returns a tuple of generator
        (for reading the image file) and image_size

        :param location `glance_store.location.Location` object, supplied
                        from glance_store.location.get_location_from_uri()
        """

        image = location.store_location.image_id

        try:
            headers, data_iterator = self.sproxyd_client.get_object(image)
        except scality_sproxyd_client.exceptions.SproxydException as exc:
            reason = _LE("Remote server where the image %s is present "
                         "is unavailable : %r")
            LOG.error(reason, image, exc)
            raise exceptions.RemoteServiceUnavailable()

        content_length = headers['Content-length']

        class ResponseIndexable(backend.Indexable):
            def another(self):
                try:
                    return self.wrapped.next()
                except StopIteration:
                    return ''

        return (ResponseIndexable(data_iterator, content_length),
                content_length)

    @capabilities.check
    def add(self, image_id, image_file, image_size, context=None):
        """
        Stores an image file with supplied identifier to the backend
        storage system and returns a tuple containing information
        about the stored image.

        :param image_id: The opaque image identifier
        :param image_file: The image data to write, as a file-like object
        :param image_size: The size of the image data to write, in bytes

        :retval tuple of URL in backing store, bytes written, and checksum
        :raises `glance_store.exceptions.Duplicate` if the image already
                existed
        """

        store_location = StoreLocation({'image_id': image_id}, self.conf)
        checksum = hashlib.md5()

        headers = {
            'transfer-encoding': 'chunked',
            # Exclusive PUT - return 412 Precondition Failed if any object with
            # the requested key already exists in the Ring.
            'If-None-Match': '*'
        }
        try:
            conn, release_conn = \
                self.sproxyd_client.get_http_conn_for_put(image_id, headers)
        except scality_sproxyd_client.exceptions.SproxydException as exc:
            LOG.error(_LE("Error while trying to get an HTTP connection : "
                          "%r"), exc)
            # The full stack trace will be logged by
            # glance/api/v1/upload_utils.py
            raise

        # If the image is read from STDIN, glance-client won't send the
        # Content-Length so image_size will be 0. Let's calculate the image
        # size ourself
        actual_image_size = 0

        try:
            conn.sock.settimeout(conn.timeout)
            for chunk in utils.chunkreadable(image_file, self.CHUNKSIZE):
                chunk_length = len(chunk)
                actual_image_size += chunk_length
                conn.send('%x\r\n%s\r\n' % (chunk_length, chunk))
                checksum.update(chunk)
            conn.send('0\r\n\r\n')
            resp = conn.getresponse()
        except Exception:
            conn.close()
            conn = None
            LOG.exception(_LE("Error during upload of image %s to the Ring"),
                          image_id)
            # Note(zhiyan): clean up already received data when
            # error occurs.
            with excutils.save_and_reraise_exception():
                self.sproxyd_client.del_object(image_id)

        # Drain connection
        resp.read()
        release_conn()

        if resp.status == 200:
            LOG.info(_LI("Uploaded image %(iid)s, md5 %(md)s, length %(len)s, "
                         "chord key %(key)s to Sproxyd"),
                     dict(iid=image_id, md=checksum.hexdigest(),
                          key=resp.getheader('X-Scal-Ring-Key'),
                          len=actual_image_size))
        elif resp.status == 412:
            LOG.error(_LE("Uploading image %(iid)s to Sproxyd failed. "
                          "%(status)s %(reason)s : %(detail)s. There's "
                          "already an object at key=%(key)s"),
                      dict(iid=image_id,
                           status=resp.status, reason=resp.reason,
                           detail=resp.getheader('X-Scal-Ring-Status',
                                                 'Error'),
                           key=resp.getheader('X-Scal-Ring-Key')))
            raise exceptions.Duplicate(image=store_location.get_uri())
        else:
            LOG.error(_LE("Uploaded image %(iid)s resulted in unexpected "
                          "status %(status)s %(reason)s : %(detail)s"),
                      dict(iid=image_id,
                           status=resp.status, reason=resp.reason,
                           detail=resp.getheader('X-Scal-Ring-Status',
                                                 'Error')))
            try:
                self.sproxyd_client.del_object(image_id)
            except scality_sproxyd_client.exceptions.SproxydException:
                # We silent this because this exception could be a
                # a side effect of the failed previous operation
                pass
            raise exceptions.BackendException()

        return (store_location.get_uri(), actual_image_size,
                checksum.hexdigest(), {})

    @capabilities.check
    def delete(self, location, context=None):
        """
        Takes a `glance_store.location.Location` object that indicates
        where to find the image file to delete

        :location `glance_store.location.Location` object, supplied
                  from glance_store.location.get_location_from_uri()

        :raises NotFound if image does not exist
        """
        image = location.store_location.image_id

        # Deleting an object that didn't exist returns a '200'
        # To be able to raise a NotFound, we need to do a HEAD just before
        # the DELETE.
        try:
            self.sproxyd_client.head(image)
        except scality_sproxyd_client.exceptions.SproxydHTTPException as exc:
            if exc.http_status == 404:
                msg = _("Image %s does not exist in the Ring") % image
                raise exceptions.NotFound(message=msg)
            else:
                raise

        self.sproxyd_client.del_object(image)
        LOG.info(_LI("The image %s was deleted from the Ring"), image)
