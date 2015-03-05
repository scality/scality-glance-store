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

import mock
import unittest
import uuid

import glance_store.exceptions
import glance_store.tests.base

import scality_sproxyd_client.exceptions

from scality_glance_store.store import StoreLocation
from scality_glance_store.store import Store


class MockLocation(object):
    def __init__(self, _uuid):
        self.store_location = StoreLocation({'image_id': _uuid}, {})


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

        self.set_sproxyd_endpoints_in_conf(['http://localhost:81/proxy/path/'])

    def set_sproxyd_endpoints_in_conf(self, endpoints):
        self.conf.set_override('scality_sproxyd_endpoints', endpoints,
                               group='glance_store')

    def test_init(self):
        endpoints = set(['http://h1:81/proxy/', 'http://h2:81/proxy/'])
        self.set_sproxyd_endpoints_in_conf(endpoints)

        store = Store(self.conf)
        self.assertEqual(endpoints, store.sproxyd_client.sproxyd_urls_set)

    def test_get_schemes(self):
        store = Store(self.conf)

        self.assertEqual(('scality',), store.get_schemes())

    @mock.patch('scality_sproxyd_client.sproxyd_client.SproxydClient.'
                'get_object', side_effect=scality_sproxyd_client.exceptions.
                SproxydException())
    def test_get_with_sproxyd_exception(self, mock_get_object):
        store = Store(self.conf)

        _uuid = str(uuid.uuid4())
        location = MockLocation(_uuid)

        self.assertRaises(glance_store.exceptions.RemoteServiceUnavailable,
                          store.get, location)
        mock_get_object.assert_called_once_with(_uuid)

    def test_get(self):
        store = Store(self.conf)

        _uuid = str(uuid.uuid4())
        location = MockLocation(_uuid)

        data = '*'*80
        headers = {'Content-length': len(data)}

        def gen():
            yield data

        mock_get_object = mock.Mock()
        mock_get_object.return_value = headers, gen()

        with mock.patch('scality_sproxyd_client.sproxyd_client.SproxydClient.'
                        'get_object', mock_get_object):
            resp, content_length = store.get(location)

        mock_get_object.assert_called_once_with(_uuid)
        self.assertEqual(len(data), content_length)
        self.assertEqual(data, resp.another())
        self.assertEqual('', resp.another())

    @mock.patch('scality_sproxyd_client.sproxyd_client.SproxydClient.head',
                side_effect=scality_sproxyd_client.exceptions.
                SproxydHTTPException('', http_status=404))
    def test_delete_with_sproxyd_exception_404(self, mock_head):
        store = Store(self.conf)

        _uuid = str(uuid.uuid4())
        location = MockLocation(_uuid)

        self.assertRaises(glance_store.exceptions.NotFound, store.delete,
                          location)
        mock_head.assert_called_once_with(_uuid)

    @mock.patch('scality_sproxyd_client.sproxyd_client.SproxydClient.head',
                side_effect=scality_sproxyd_client.exceptions.
                SproxydHTTPException('', http_status=500))
    def test_delete_with_sproxyd_exception_500(self, mock_head):
        store = Store(self.conf)

        _uuid = str(uuid.uuid4())
        location = MockLocation(_uuid)

        self.assertRaises(scality_sproxyd_client.exceptions.
                          SproxydHTTPException, store.delete, location)
        mock_head.assert_called_once_with(_uuid)

    @mock.patch('scality_sproxyd_client.sproxyd_client.SproxydClient.head',
                mock.Mock())
    @mock.patch('scality_sproxyd_client.sproxyd_client.SproxydClient.'
                'del_object')
    def test_delete(self, mock_del_object):
        store = Store(self.conf)

        _uuid = str(uuid.uuid4())
        location = MockLocation(_uuid)

        store.delete(location)
        mock_del_object.assert_called_once_with(_uuid)


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
