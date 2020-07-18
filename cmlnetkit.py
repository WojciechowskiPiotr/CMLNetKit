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
                                  help='Lab ID. If not specified then returns list of labs')
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
    group_changes.add_argument('-lo_subnet',
                               help='Subnet for the Loopback ip addresses assignment, must be provided in format as '
                                    'subnet/mask. If mask not provided default mask for subnet is used.'
                                    'If none provided the default 10.0.0.0/24 is used. Loopback '
                                    'addresses are always /32',
                               dest="loopback_subnet", default="10.0.0.0/24")

    CMLNetKit.CMLNetKit(CMLNetKitConfig.CMLNetKitConfig(parser.parse_args()))


if __name__ == '__main__':
    main()
