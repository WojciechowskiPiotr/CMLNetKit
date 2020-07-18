# -*- coding: utf-8 -*-
# (c) 2020 Piotr Wojciechowski <piotr@it-playground.pl>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import argparse
import netaddr


class CMLNetKitConfig:
    """
    Initializes a CMLNetKitConfig instance. This class is used to collect all parameters provided by
    argparse and in future perform some additional checkup.

    :param args: List of arguments parsed by parse_args().
    :type args: argparse.Namespace
    """

    # Connection definition
    host = None
    lab_id = None
    port = None
    username = None
    password = None
    ssl_verify = True
    dry_run = False

    # Flag if requested to change "External Connection" objects
    update_bridge = False
    # Flag if requested to change the Loopback interfaces configuration
    update_loopback = False
    loopback_subnet = None

    def __init__(self, args):
        self.host = args.host
        self.username = args.username
        self.password = args.password
        self.port = args.port
        self.ssl_verify = args.ssl_verify

        if args.lab_id is not None:
            self.lab_id = args.lab_id

        if args.update_bridge is True:
            self.update_bridge = True

        if args.update_loopback is True:
            self.update_loopback = True

        if args.dry_run is True:
            self.dry_run = True

        # Initialize the variable that stores subnet for adressing Loopback interfaces.
        # We need to check if /32 mask was not provided, the subnet is IPv4, unicast and provided
        # in correct CIDR format. In case any requirement is violated the program cannot continue
        if type(args.loopback_subnet) is not str:
            raise TypeError
        try:
            prefix = netaddr.IPNetwork(args.loopback_subnet, version=4)
        except ValueError as e:
            print("Parameter error: loopback_subnet:", e.data)
            exit(0)
        except netaddr.AddrFormatError as e:
            print("Parameter error: loopback_subnet: Address format error")
            exit(0)
        else:
            if not prefix.is_unicast():
                print("Parameter error: loopback_subnet: Non-unicast address")
                exit(0)
            if prefix.prefixlen == 32:
                print("Parameter error: loopback_subnet: Host address provided")
                exit(0)
            self.loopback_subnet = args.loopback_subnet
