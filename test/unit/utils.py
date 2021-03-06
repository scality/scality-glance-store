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

"""A collection of functions that helps running unit tests"""

import re
import unittest


def assertRaisesRegexp(expected_exception, expected_regexp,
                       callable_obj, *args, **kwargs):
    """Asserts that the message in a raised exception matches a regexp."""
    try:
        callable_obj(*args, **kwargs)
    except expected_exception as exc_value:
        if not re.search(expected_regexp, str(exc_value)):
            # We accept both `string` and compiled regex object as 2nd
            # argument to assertRaisesRegexp
            pattern = getattr(expected_regexp, 'pattern', expected_regexp)
            raise unittest.TestCase.failureException(
                '"%s" does not match "%s"' %
                (pattern, str(exc_value)))
    else:
        if hasattr(expected_exception, '__name__'):
            excName = expected_exception.__name__
        else:
            excName = str(expected_exception)
        raise unittest.TestCase.failureException("%s not raised" % excName)
