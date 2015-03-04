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

import unittest
import uuid

import glance_store.exceptions

from scality_glance_store.store import StoreLocation
from scality_glance_store.store import Store


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


class TestStore(unittest.TestCase):
    """Tests for scality_glance_store.store.Store"""


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
