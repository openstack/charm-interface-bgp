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
import mock
import yaml

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

    _network_get_side_effect = [
        yaml.load('''
bind-addresses:
- macaddress: 52:54:00:0a:97:58
  interfacename: ens6
  addresses:
  - address: 172.16.122.251
    cidr: 172.16.122.0/24
ingress-addresses:
- 172.16.122.251
'''),  # bgpserver
        yaml.load('''
bind-addresses:
- macaddress: 52:54:01:0a:97:58
  interfacename: ens7
  addresses:
  - address: 172.16.100.1
    cidr: 172.16.100.0/30
  - address: 2001:db8:100::1:0:0
    cidr: 2001:db8:100::/64
ingress-addresses:
- 172.16.100.1
- 2001:db8:100::1:0:0
'''),  # ptp0
        yaml.load('''
bind-addresses:
- macaddress: 52:54:02:0a:97:58
  interfacename: ens8
  addresses:
  - address: 172.16.110.1
    cidr: 172.16.110.0/30
  - address: 2001:db8:110::1:0:0
    cidr: 2001:db8:110::/64
ingress-addresses:
- 172.16.110.1
- 2001:db8:110::1:0:0
'''),  # ptp1
        yaml.load('''
bind-addresses:
- macaddress: 52:54:03:0a:97:58
  interfacename: ens9
  addresses:
  - address: 172.16.120.1
    cidr: 172.16.120.0/30
  - address: 2001:db8:120::1:0:0
    cidr: 2001:db8:120::/64
ingress-addresses:
- 172.16.120.1
- 2001:db8:120::1:0:0
'''),  # ptp2
        yaml.load('''
bind-addresses:
- macaddress: 52:54:00:0a:97:58
  interfacename: ens6
  addresses:
  - address: 172.16.122.251
    cidr: 172.16.122.0/24
ingress-addresses:
- 172.16.122.251
'''),  # ptp3
        yaml.load('''
bind-addresses:
- macaddress: 52:54:00:0a:97:58
  interfacename: ens6
  addresses:
  - address: 172.16.122.251
    cidr: 172.16.122.0/24
ingress-addresses:
- 172.16.122.251
'''),  # lan0
    ]

    _relation = mock.Mock()
    _relation.relation_id = 0
    _relation.units = []
    _relation.to_publish = {}

    def test_publish_info(self):
        self.maxDiff = None
        self.patch_object(provides, 'ch_core')
        self.ch_core.hookenv.unit_get.return_value = '172.16.122.251'
        self.ch_core.hookenv.network_get.side_effect = \
            self._network_get_side_effect
        endpoint = provides.BGPEndpoint('bgpserver')
        endpoint._relations = [self._relation]
        endpoint.publish_info(bindings=['ptp0', 'ptp1', 'ptp2', 'ptp3',
                                        'lan0'])
        self.assertEqual(
            endpoint.relations[0].to_publish,
            {
                'asn': 4279270138,
                'bindings': [
                    {
                        'address': '172.16.100.1',
                        'cidr': '172.16.100.0/30'
                    },
                    {
                        'address': '2001:db8:100::1:0:0',
                        'cidr': '2001:db8:100::/64'
                    },
                    {
                        'address': '172.16.110.1',
                        'cidr': '172.16.110.0/30'
                    },
                    {
                        'address': '2001:db8:110::1:0:0',
                        'cidr': '2001:db8:110::/64'
                    },
                    {
                        'address': '172.16.120.1',
                        'cidr': '172.16.120.0/30'
                    },
                    {
                        'address': '2001:db8:120::1:0:0',
                        'cidr': '2001:db8:120::/64'
                    },
                ],
                'passive': False,
            }
        )

    def test_get_received_info(self):
        self.maxDiff = None
        self.patch_object(provides, 'ch_core')
        self.patch_object(provides, 'ch_net_ip')
        self.ch_core.hookenv.unit_get.return_value = '172.16.122.251'
        self.ch_core.hookenv.network_get.side_effect = \
            self._network_get_side_effect
        endpoint = provides.BGPEndpoint('bgpserver')
        endpoint._relations = [self._relation]
        endpoint.publish_info(bindings=['ptp0', 'ptp1', 'ptp2', 'ptp3',
                                        'lan0'])
        _unit = mock.Mock()
        _unit.unit_name = None
        _unit.received = endpoint.relations[0].to_publish
        endpoint._relations[0].units.append(_unit)
        neighbors = endpoint.get_received_info()
        self.assertEqual(neighbors, [
                {
                    'remote_unit_name': None,
                    'links': [
                        {
                            'cidr': '172.16.100.0/30',
                            'local': self.ch_net_ip.get_address_in_network(
                                '172.16.100.0/30'
                            ),
                            'remote': '172.16.100.1'
                        },
                        {
                            'cidr': '2001:db8:100::/64',
                            'local': self.ch_net_ip.get_address_in_network(
                                '2001:db8:100::/64'
                            ),
                            'remote': '2001:db8:100::1:0:0'
                        },
                        {
                            'cidr': '172.16.110.0/30',
                            'local': self.ch_net_ip.get_address_in_network(
                                '172.16.110.0/30'
                            ),
                            'remote': '172.16.110.1'
                        },
                        {
                            'cidr': '2001:db8:110::/64',
                            'local': self.ch_net_ip.get_address_in_network(
                                '2001:db8:110::/64'
                            ),
                            'remote': '2001:db8:110::1:0:0'
                        },
                        {
                            'cidr': '172.16.120.0/30',
                            'local': self.ch_net_ip.get_address_in_network(
                                '172.16.120.0/30'
                            ),
                            'remote': '172.16.120.1'
                        },
                        {
                            'cidr': '2001:db8:120::/64',
                            'local': self.ch_net_ip.get_address_in_network(
                                '2001:db8:120::/64'
                            ),
                            'remote': '2001:db8:120::1:0:0'
                        },
                    ],
                    'passive': False,
                    'asn': 4279270138,
                    'relation_id': 0,
                },
            ]
        )
