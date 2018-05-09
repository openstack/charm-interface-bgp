# Copyright 2018 Canonical Ltd.
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

import unit_tests.utils as ut_utils
import provides


class TestBGPProvides(ut_utils.BaseTestCase):
    def test_generate_asn_min(self):
        self.patch_object(provides, 'ch_core')
        self.ch_core.hookenv.unit_get.return_value = '0.0.0.0'
        endpoint = provides.BGPEndpoint('bgpserver')
        asn = endpoint.generate_asn()
        self.assertEqual(asn, 4211081215)

    def test_generate_asn_max(self):
        self.patch_object(provides, 'ch_core')
        self.ch_core.hookenv.unit_get.return_value = '255.255.255.255'
        endpoint = provides.BGPEndpoint('bgpserver')
        asn = endpoint.generate_asn()
        self.assertEqual(asn, 4294967294)
