# -*- coding: utf-8 -*-
# (c) 2020 Piotr Wojciechowski <piotr@it-playground.pl>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
import argparse

from CMLNetKit.AutoNetKit import CMLNetKit
from CMLNetKit.AutoNetKit import CMLNetKitConfig


def main():
    parser = argparse.ArgumentParser()

    group_connection = parser.add_argument_group("Connection options")
    group_changes = parser.add_argument_group("Configuration changes")

    group_connection.add_argument('-H', '--host', type=str, dest='host', help='CML2.0 host address')
    group_connection.add_argument('-l', '--lab', type=str, dest='lab_id',
                                  help='Lab ID')
    group_connection.add_argument('--list-labs', dest='list_labs',
                                  help='List the ID of existing labs', default=False, action="store_true")
    group_connection.add_argument('--list-ips', dest='list_ips',
                                  help='List the IP addresses configured on L3 links', default=False,
                                  action="store_true")
    group_connection.add_argument('-P', '--port', type=int, help='CML 2.0 API port (default 443)', dest='port',
                                  default=443)
    group_connection.add_argument('-u', '--username', type=str, help='CML 2.0 API username (default "virl2")',
                                  dest='username', default="virl2")
    group_connection.add_argument('-p', '--password', type=str, help='CML 2.0 API password (default "virl2")',
                                  dest='password',
                                  default="virl2")
    group_connection.add_argument('--no-ssl-verification',
                                  help='Disable the SSL certification verification on the CML2 server',
                                  dest='ssl_verify',
                                  default=True, action="store_false")
    group_connection.add_argument('--dry-run', help="Don't apply any changes to CML2 server.",
                                  dest='dry_run',
                                  default=False, action="store_true")
    group_changes.add_argument('-b',
                               help='Changing all "External Connection" objects configuration to "Bridge"',
                               dest="update_bridge", default=False, action="store_true")
    group_changes.add_argument('-lo',
                               help='Readdress all Loopback0 interfaces without IPv4 address',
                               dest="update_loopback", default=False, action="store_true")
    group_changes.add_argument('--lo-subnet',
                               help='Subnet for the Loopback ip addresses assignment, must be provided in format as '
                                    'subnet/mask. If mask not provided default mask for subnet is used.'
                                    'If none provided the default 10.0.0.0/24 is used. Loopback '
                                    'addresses are always /32',
                               dest="loopback_subnet", default="10.0.0.0/24")
    group_changes.add_argument('-mgmt',
                               help='Readdress all management interfaces without IPv4 address. If device do not'
                                    'have dedicated management interface then first GigabitEthernet is used.',
                               dest="update_mgmt", default=False, action="store_true")
    group_changes.add_argument('--mgmt-range',
                               help='Contiguous range of IP addresses must be provided. As argument values provide '
                                    'first and last IP address of the range',
                               nargs=2, metavar=('MGMT_IP_LOW', "MGMT_IP_HIGH"), dest="mgmt_range")
    group_changes.add_argument('--peer-subnet',
                               help='Subnet for the ip addresses assignment for direct connections betweend devices,'
                                    'must be provided in format as subnet/mask. If mask not provided the /24 is used.'
                                    'Direct connections betweend devices are addressed with /30 mask',
                               dest="peer_subnet")
    group_changes_mask_prefixlen = group_changes.add_mutually_exclusive_group()
    group_changes_mask_prefixlen.add_argument('--mgmt-netmask',
                                              help='Subnet mask that needs to be assigned to management interfaces IP '
                                                   'addresses on devices. Mask must be provided in standard netmask '
                                                   'notation 255.255.255.0 If neither -mgmt-netmask nor '
                                                   '-mgmt-prefixlen is provided then /24 prefixlen (mask of '
                                                   '255.255.255.0) is assigned.',
                                              dest="mgmt_netmask", type=str)
    group_changes_mask_prefixlen.add_argument('--mgmt-prefixlen',
                                              help='Subnet mask that needs to be assigned to management interfaces IP '
                                                   'addresses on devices. Prefixlen must be provided as integer '
                                                   'between 0 and 32. If neither -mgmt-netmask nor -mgmt-prefixlen is '
                                                   'provided then /24 prefixlen (mask of 255.255.255.0) is assigned.',
                                              dest="mgmt_prefixlen", type=int)

    p = parser.parse_args()
    if (p.mgmt_netmask or p.mgmt_prefixlen) and not p.mgmt_range:
        parser.error("Missing the --mgmt-range parameter required when providing either --mgmt-netmask or "
                     "--mgmt-prefixlen")

    CMLNetKit.CMLNetKit(CMLNetKitConfig.CMLNetKitConfig(p))


if __name__ == '__main__':
    main()
