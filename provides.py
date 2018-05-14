# Copyright 2018 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import charmhelpers.core as ch_core
import charmhelpers.contrib.network.ip as ch_net_ip
from charms import reactive
import netaddr


class BGPEndpoint(reactive.Endpoint):
    def generate_asn(self):
        """
        Generate unique 32-bit Private Use [RFC6996] ASn.

        This is useful to automate configuration of BGP routers that is part
        of a Clos Network Topology with a Layer 3-Only routed design. [RFC7938]

        Assumption:
        - Unit has a IPv4 address and it is unique to the deployment.

        Implementation:
        - A private 32-bit ASn has a range of 4 200 000 000 - 4 294 967 294
          which leaves us with 94 967 294 possible endpoints.
        - Within a deployment it is less likelly that the 4 most significant
          bits of the IP address differ between units.
        - If we cap the 4 most significant bits of the IPv4 address to be
          within the range of 0 and 4, the decimal representation of the
          resulting IPv4 address fits nicely into that range.

        Note:
        - This implementation generates ASn in the following range:
          4 211 081 215 - 4 294 967 294
        - Leaving the following range for any static configuration needs:
          4 200 000 000 - 4 211 081 214
        """
        asn_base = 4211081215
        mask = netaddr.IPAddress('4.255.255.255')
        unit_ip = netaddr.IPAddress(
                ch_core.hookenv.unit_get('private-address'))
        masked_ip = unit_ip & mask

        asn = asn_base + int(masked_ip)

        return asn

    def publish_info(self, asn=None, passive=False, bindings=None):
        """
        Publish the AS Number and IP address of any extra-bindings of this
        BGP Endpoint over the relationship.

        If no AS Number is provided a unique 32-bit Private Use [RFC6996] ASn
        will be generated.

        :param asn:      AS Number to publish.  Autogenerated if not provided.
        :param passive:  Advertise that we wish to be configured as passive
                         neighbour.
        :param bindings: List bindings advertised as links to speak BGP on.
        """
        if asn:
            myasn = asn
        else:
            myasn = self.generate_asn()

        # network_get will return addresses for bindings regardless of them
        # being bound to a network space.  detect actual space bindings by
        # comparing returned addresses to what we have for the relation itself.
        for relation in self.relations:
            rel_network = ch_core.hookenv.network_get(
                    self.expand_name('{endpoint_name}'),
                    relation_id=relation.relation_id)
            rel_addrs = [a['address']
                         for a in
                         rel_network['bind-addresses'][0]['addresses']]
            actual_bindings = []
            if bindings is None:
                continue
            for binding in bindings:
                bind_network = ch_core.hookenv.network_get(
                        binding,
                        relation_id=relation.relation_id)
                bind_addrs = [a['address']
                              for a in
                              bind_network['bind-addresses'][0]['addresses']]
                if not set(bind_addrs).issubset(set(rel_addrs)):
                    actual_bindings.extend(
                            bind_network['bind-addresses'][0]['addresses'])
            relation.to_publish['asn'] = myasn
            relation.to_publish['bindings'] = actual_bindings
            relation.to_publish['passive'] = passive
            ch_core.hookenv.log("to_publish: '{}'".format(relation.to_publish))

    def get_received_info(self):
        neighbors = []
        for relation in self.relations:
            for unit in relation.units:
                if not ('asn' in unit.received and
                        'bindings' in unit.received):
                    ch_core.hookenv.log('Skip get_received_info() '
                                        'relation incomplete...',
                                        level=ch_core.hookenv.DEBUG)
                    continue
                links = []
                for addrinfo in unit.received['bindings']:
                    # filter list of networks to those we have interfaces
                    # configured for
                    ip = ch_net_ip.get_address_in_network(addrinfo['cidr'])
                    if ip:
                        links.append(
                                {'local': ip,
                                 'remote': addrinfo['address'],
                                 'cidr': addrinfo['cidr']}
                                )
                ch_core.hookenv.log("links: '{}'".format(links))
                neighbors.append({
                    'asn': unit.received['asn'],
                    'links': links,
                    'relation_id': relation.relation_id,
                    'remote_unit_name': unit.unit_name,
                    'passive': unit.received['passive'],
                    })
        return neighbors
