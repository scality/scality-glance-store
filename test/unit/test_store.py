# Copyright (c) 2015 Scality
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for Scality Glance Store"""

import hashlib
import logging
import mock
import StringIO
import unittest
import uuid

import glance_store.exceptions
import glance_store.tests.base

import scality_sproxyd_client.exceptions

from scality_glance_store.store import StoreLocation
from scality_glance_store.store import Store
from . import utils

logging.getLogger('stevedore.extension').level = logging.INFO


class MockLocation(object):
    def __init__(self, image_id):
        self.store_location = StoreLocation({'image_id': image_id}, {})


class TestStoreLocation(unittest.TestCase):
    """Tests for scality_glance_store.store.StoreLocation"""

    def test_process_specs(self):
        image_id = str(uuid.uuid4())
        store_location = StoreLocation({'image_id': image_id}, {})

        self.assertEqual(image_id, store_location.image_id)

    def test_get_uri(self):
        image_id = str(uuid.uuid4())
        store_location = StoreLocation({'image_id': image_id}, {})

        self.assertEqual('scality://%s' % image_id, store_location.get_uri())

    def test_parse_uri(self):
        image_id_1 = str(uuid.uuid4())
        store_location = StoreLocation({'image_id': image_id_1}, {})

        image_id_2 = str(uuid.uuid4())
        store_location.parse_uri('scality://%s' % image_id_2)

        self.assertEqual(image_id_2, store_location.image_id)


@mock.patch('eventlet.spawn', mock.Mock())
class TestStore(glance_store.tests.base.StoreBaseTest):
    """Tests for scality_glance_store.store.Store"""

    def setUp(self):
        """Establish a clean test environment."""
        super(TestStore, self).setUp()

        self.set_sproxyd_endpoints_in_conf(['http://h0:81/proxy/path/',
                                            'http://h1:82/proxy/path/'])

    def set_sproxyd_endpoints_in_conf(self, endpoints):
        self.conf.set_override('scality_sproxyd_endpoints', endpoints,
                               group='glance_store')

    def _mock_get_object(self, reply):
        """Create a mock for `SproxydClient.get_object`"""
        def response():
            yield reply

        m = mock.Mock()
        headers = {'Content-Length': len(reply)}
        m.return_value = headers, response()
        return m

    def test_init_with_no_endpoint(self):
        self.set_sproxyd_endpoints_in_conf("")
        self.assertRaises(glance_store.exceptions.BadStoreConfiguration,
                          Store, self.conf)

    def test_init(self):
        endpoints = set(['http://h1:81/proxy/', 'http://h2:81/proxy/'])
        self.set_sproxyd_endpoints_in_conf(endpoints)

        store = Store(self.conf)

        actual_endpoints = frozenset(
            store._sproxyd_client.get_next_endpoint().geturl()
            for _ in endpoints)

        self.assertEqual(endpoints, actual_endpoints)

    def test_get_schemes(self):
        store = Store(self.conf)

        self.assertEqual(('scality',), store.get_schemes())

    @mock.patch(
        'scality_sproxyd_client.sproxyd_client.SproxydClient.get_object',
        side_effect=scality_sproxyd_client.exceptions.SproxydException)
    def test_get_with_sproxyd_exception(self, mock_get_object):
        store = Store(self.conf)

        image_id = str(uuid.uuid4())
        location = MockLocation(image_id)

        self.assertRaises(glance_store.exceptions.RemoteServiceUnavailable,
                          store.get, location)
        mock_get_object.assert_called_once_with(image_id)

    def test_get(self):
        store = Store(self.conf)

        image_id = str(uuid.uuid4())
        location = MockLocation(image_id)

        data = '*'*80
        mock_get_object = self._mock_get_object(data)

        with mock.patch(
                'scality_sproxyd_client.sproxyd_client.'
                'SproxydClient.get_object',
                mock_get_object):
            resp, content_length = store.get(location)

        mock_get_object.assert_called_once_with(image_id)
        self.assertEqual(len(data), content_length)
        self.assertEqual(data, resp.another())
        self.assertEqual('', resp.another())

    @mock.patch(
        'scality_sproxyd_client.sproxyd_client.SproxydClient.head',
        side_effect=scality_sproxyd_client.exceptions.SproxydHTTPException(
            '', http_status=404))
    def test_delete_with_sproxyd_exception_404(self, mock_head):
        store = Store(self.conf)

        image_id = str(uuid.uuid4())
        location = MockLocation(image_id)

        self.assertRaises(glance_store.exceptions.NotFound, store.delete,
                          location)
        mock_head.assert_called_once_with(image_id)

    @mock.patch(
        'scality_sproxyd_client.sproxyd_client.SproxydClient.head',
        side_effect=scality_sproxyd_client.exceptions.SproxydHTTPException(
            '', http_status=500))
    def test_delete_with_sproxyd_exception_500(self, mock_head):
        store = Store(self.conf)

        image_id = str(uuid.uuid4())
        location = MockLocation(image_id)

        self.assertRaises(
            scality_sproxyd_client.exceptions.SproxydHTTPException,
            store.delete, location)
        mock_head.assert_called_once_with(image_id)

    @mock.patch('scality_sproxyd_client.sproxyd_client.SproxydClient.head',
                mock.Mock())
    @mock.patch(
        'scality_sproxyd_client.sproxyd_client.SproxydClient.del_object')
    def test_delete(self, mock_del_object):
        store = Store(self.conf)

        image_id = str(uuid.uuid4())
        location = MockLocation(image_id)

        store.delete(location)
        mock_del_object.assert_called_once_with(image_id)

    @mock.patch('scality_sproxyd_client.sproxyd_client.SproxydClient.'
                'get_http_conn_for_put', side_effect=scality_sproxyd_client.
                exceptions.SproxydException())
    @mock.patch('scality_glance_store.store.LOG.error')
    def test_add_with_sproxyd_exception_in_get_conn(self, mock_log,
                                                    mock_get_conn):
        store = Store(self.conf)

        image_id = str(uuid.uuid4())
        headers = {
            'transfer-encoding': 'chunked',
            'If-None-Match': '*'
        }

        self.assertRaises(scality_sproxyd_client.exceptions.SproxydException,
                          store.add, image_id, None, None)
        mock_get_conn.assert_called_once_with(image_id, headers)
        mock_log.assert_called_once_with(mock.ANY, mock_get_conn.side_effect)

    @mock.patch('scality_sproxyd_client.sproxyd_client.SproxydClient.'
                'get_http_conn_for_put',
                return_value=(mock.Mock(), mock.Mock()))
    @mock.patch('glance_store.common.utils.chunkreadable',
                side_effect=Exception)
    @mock.patch(
        'scality_sproxyd_client.sproxyd_client.SproxydClient.del_object')
    def test_add_with_exception_in_put(self, mock_del_object,
                                       mock_chunkreadable,
                                       mock_get_http_conn_for_put):
        store = Store(self.conf)

        image_id = str(uuid.uuid4())
        self.assertRaises(Exception, store.add, image_id, None, None)

        mock_chunkreadable.assert_called_once_with(None, Store.CHUNKSIZE)

        conn, release_conn = mock_get_http_conn_for_put.return_value
        conn.close.assert_called_once_with()
        self.assertFalse(release_conn.called)

        mock_del_object.assert_called_once_with(image_id)

    @mock.patch('scality_sproxyd_client.sproxyd_client.SproxydClient.'
                'get_http_conn_for_put', return_value=(mock.Mock(),
                                                       mock.Mock()))
    def test_add(self, mock_get_http_conn_for_put):
        conn, release_conn = mock_get_http_conn_for_put.return_value
        conn.getresponse.return_value = mock.Mock(status=200)

        image_id = str(uuid.uuid4())
        file_contents = "chunk00000remainder"
        image_file = StringIO.StringIO(file_contents)

        store = Store(self.conf)
        img_uri, img_size, img_checksum, _ = store.add(image_id, image_file,
                                                       None)

        # Assert data has been written to Sproxyd
        calls = [mock.call('%x\r\n%s\r\n' % (len(file_contents),
                                             file_contents)),
                 mock.call('0\r\n\r\n')]
        conn.send.assert_has_calls(calls)

        # Assert the response has been read and the connection drained
        # and release
        conn.getresponse.assert_called_oncewith()
        conn.getresponse.read.assert_called_oncewith()
        release_conn.assert_called_oncewith()

        # Assert the return values of `store.add` are connect
        self.assertEqual('scality://%s' % image_id, img_uri)
        self.assertEqual(len(file_contents), img_size)
        self.assertEqual(hashlib.md5(image_file.getvalue()).hexdigest(),
                         img_checksum)

    @mock.patch('scality_sproxyd_client.sproxyd_client.SproxydClient.'
                'get_http_conn_for_put', return_value=(mock.Mock(),
                                                       mock.Mock()))
    def test_add_with_response_412(self, mock_get_http_conn_for_put):
        conn, release_conn = mock_get_http_conn_for_put.return_value
        conn.getresponse.return_value = mock.Mock(status=412)

        image_id = str(uuid.uuid4())
        image_file = StringIO.StringIO("chunk00000remainder")

        store = Store(self.conf)
        msg = r'scality://%s .*already exists' % image_id
        utils.assertRaisesRegexp(glance_store.exceptions.Duplicate, msg,
                                 store.add, image_id, image_file, None)

    @mock.patch('scality_sproxyd_client.sproxyd_client.SproxydClient.'
                'get_http_conn_for_put', return_value=(mock.Mock(),
                                                       mock.Mock()))
    @mock.patch(
        'scality_sproxyd_client.sproxyd_client.SproxydClient.del_object',
        side_effect=scality_sproxyd_client.exceptions.SproxydException)
    def test_add_with_response_500(self, mock_del_object,
                                   mock_get_http_conn_for_put):
        conn, release_conn = mock_get_http_conn_for_put.return_value
        conn.getresponse.return_value = mock.Mock(status=500)

        image_id = str(uuid.uuid4())
        image_file = StringIO.StringIO("chunk00000remainder")

        store = Store(self.conf)
        self.assertRaises(glance_store.exceptions.BackendException,
                          store.add, image_id, image_file, None)
        mock_del_object.assert_called_once_with(image_id)


def test_store_location_parse_uri_with_bad_uri():

    def assert_bad_store_uri_is_raised(uri):
        image_id = str(uuid.uuid4())
        store_location = StoreLocation({'image_id': image_id}, {})

        try:
            store_location.parse_uri(uri)
        except glance_store.exceptions.BadStoreUri:
            pass
        else:
            raise unittest.TestCase.failureException("BadStoreUri not raised")

    for uri in ['fake://', 'scality://', 'scality:///']:
        yield assert_bad_store_uri_is_raised, uri
