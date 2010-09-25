# -*- coding: utf-8 -*-
#
# Copyright 2010 Tobias Rodäbel
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Instruments for measuring the memory footprint of a GAE application."""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from django.utils import simplejson
from google.appengine.api import memcache
from guppy import hpy

import gc


class JSONSerializable(object):
    """Base class for JSON serializable objects."""

    def __setattr__(self, attr, value):
        self.__dict__['_k_'+attr] = value

    def __getattr__(self, attr):
        return self.__dict__['_k_'+attr]

    def __repr__(self):
        data = dict([(k[3:], self.get_value(self.__dict__[k]))
                     for k in self.__dict__ if k.startswith('_k_')])
        return unicode(data)

    @classmethod
    def get_value(C, value):
        return value

    @classmethod
    def make_value(C, value):
        return value

    def EncodeJSON(self):
        """Encodes record to JSON."""

        return simplejson.dumps(eval(repr(self)))

    @staticmethod
    def make_args(args):
        return dict([(str(k), args[k]) for k in args])

    @classmethod
    def FromJSON(C, json):
        """Deserializes JSON and returns a new instance of the given class.

        Args:
            C: This class.
            json: String containing JSON.
        """

        data = simplejson.loads(json)
        return C(**dict([(str(k), C.make_value(data[k])) for k in data]))


class RecordEntry(JSONSerializable):
    """Represents a single record entry."""

    def __init__(self, module_name, name, obj_type, dominated_size):
        """Constructor.

        Args:
            module_name: Name of the module.
            name: The object name (key in module.__dict__).
            obj_type: String representing the type of the recorded object.
            dominated_size: Total size of memory that will become deallocated.
        """
        self.module_name = module_name
        self.name = name
        self.obj_type = obj_type
        self.dominated_size = dominated_size


class Record(JSONSerializable):
    """Represents a record.

    Records contain record entries.
    """

    def __init__(self, entries):
        """Constructor.

        Args:
            entries: List of RecordEntry instances.
        """
        self.entries = entries

    @classmethod
    def get_value(C, value):
        if isinstance(value, list):
            new = []
            for item in value:
                if isinstance(item, RecordEntry):
                    new.append(eval(repr(item)))
                else:
                    new.append(item)
            value = new
        return value

    @classmethod
    def make_value(C, value):
        value = value
        if isinstance(value, list):
            new = []
            for item in value:
                new.append(RecordEntry(**super(Record, C).make_args(item)))
            value = new
        return value


class Recorder(object):
    """Traces the memory usage of various appllication modules."""

    def __init__(self, config):
        """Constructor.

        Args:
            config: A middleware.Config instance.
        """
        self._config = config

    @property
    def config(self):
        return self._config

    def trace(self):
        """Records momory data.

        Uses Heapy to retrieve information about allocated memory.
        """

        gc.collect()
        hp = hpy()

        record = Record([])

        for name in self.config.get_modules():
            if name not in sys.modules:
                continue
            module_dict = sys.modules[name].__dict__
            obj_keys = sorted(set(module_dict.keys())-
                              set(self.config.IGNORE_NAMES))
            for key in obj_keys:
                obj = module_dict[key]
                iso = hp.iso(obj)
                entry = RecordEntry(name,
                                    key,
                                    obj.__class__.__name__,
                                    iso.domisize)

                record.entries.append(entry)

        # We use memcache to store records and take a straightforward
        # approach with a very simple index which is basically a counter.
        index = 1
        if not memcache.add(key=self.config.INDEX_KEY, value=index):
            index = memcache.incr(key=self.config.INDEX_KEY)
        key = self.config.RECORD_PREFIX + str(index)
        memcache.add(key=key, value=record.EncodeJSON())

    def get_raw_records(self, limit=100, offset=0):
        """Returns raw records beginning with the latest.

        Args:
            limit: Max number of records.
            offset: Offset within overall results.
        """

        curr_index = memcache.get(self.config.INDEX_KEY)
        if not curr_index:
            return []

        if curr_index < limit: limit = curr_index 

        keys = ['%i' % (curr_index-i) for i in xrange(offset, limit)]

        records = memcache.get_multi(keys=keys,
                                     key_prefix=self.config.RECORD_PREFIX)

        return [records[key] for key in keys]

    def get_records(self, limit=100, offset=0):
        """Get stored records.

        Args:
            limit: Max number of records.
            offset: Offset within overall results.

        Returns lists of RecordEntry instances.
        """
        records = self.get_raw_records(limit, offset)
        return [Record.FromJSON(record) for record in records]
