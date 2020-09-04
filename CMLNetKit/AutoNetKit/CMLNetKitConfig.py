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
    list_labs = False
    list_ips = False
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
    # Flag if requested to change interface configuration for directly connected devices
    update_peer = False
    peer_subnet = None
    # Flags for management interfaces addressing
    update_mgmt = False  # Will change to True when all management network parameters are correctly set
    mgmt_range = None
    mgmt_netmask = str
    mgmt_prefixlen = int

    def __init__(self, args):
        self.host = args.host
        self.username = args.username
        self.password = args.password
        self.port = args.port
        self.ssl_verify = args.ssl_verify

        if args.lab_id is not None:
            self.lab_id = args.lab_id

        if args.list_labs:
            self.list_labs = True

        if args.list_ips:
            self.list_ips = True

        if args.update_bridge is True:
            self.update_bridge = True

        if args.loopback_subnet:
            self.update_loopback = True

        if args.dry_run is True:
            self.dry_run = True

        # Initialize the variable that stores subnet for addressing Loopback interfaces.
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

        # Initialize range of IP addresses for management interfaces and associated subnet mask
        # Catch if provided values are even IP addresses
        if args.mgmt_range:
            try:
                if netaddr.IPAddress(args.mgmt_range[0]) > netaddr.IPAddress(args.mgmt_range[1]):
                    self.mgmt_range = netaddr.IPRange(args.mgmt_range[1], args.mgmt_range[0])
                else:
                    self.mgmt_range = netaddr.IPRange(args.mgmt_range[0], args.mgmt_range[1])
            except netaddr.AddrFormatError as e:
                raise ValueError('mgmt-range: %s' % e)

            # Check if the provided range of addresses does not overlap with any of the IPv4 reserved subnets and
            # each address is the unicast address.
            for ip_addr in self.mgmt_range:
                if ip_addr.is_reserved():
                    raise ValueError('mgmt-range: Provided IP addresses overlaps with IPv4 reserved subnets')
                if ip_addr.is_unicast() is not True:
                    raise ValueError('mgmt-range: Provided IP addresses range is not within the IPv4 '
                                     'unicast space')

            # If we receive the netmask from commandline argument then we need to check if the netmask
            # is in correct format, then convert it to prefixlen and store both values in class variables
            if args.mgmt_netmask:
                try:
                    if netaddr.IPAddress(args.mgmt_netmask).is_netmask():
                        try:
                            t = netaddr.IPNetwork(self.mgmt_range[0])
                        except netaddr.AddrFormatError as e:
                            raise ValueError('mgmt-range: %s' % e)
                    else:
                        raise ValueError('mgmt-netmask: Provided value is not a correct netmask')
                except ValueError as e:
                    raise ValueError('mgmt-netmask: %s' % e)

                self.mgmt_netmask = args.mgmt_netmask
                t.netmask = self.mgmt_netmask
                self.mgmt_prefixlen = t.prefixlen
            elif args.mgmt_prefixlen:
                if args.mgmt_prefixlen is 0:
                    raise ValueError('mgmt-prefixlen: argument value cannot be 0')
                elif args.mgmt_prefixlen in range(1, 33):
                    self.mgmt_prefixlen = args.mgmt_prefixlen
                else:
                    raise ValueError('mgmt-prefixlen: argument value must be between 1 and 32')

                try:
                    t = netaddr.IPNetwork(self.mgmt_range[0])
                except netaddr.AddrFormatError as e:
                    raise ValueError('mgmt-range: %s' % e)

                t.prefixlen = self.mgmt_prefixlen
                self.mgmt_netmask = t.netmask.__str__()
            else:
                self.mgmt_prefixlen = 24
                self.mgmt_netmask = "255.255.255.0"
            self.update_mgmt = True

        # Initialize the variable that stores subnet for addressing for directly connected interfaces.
        # We need to check if /32 mask was not provided, the subnet is IPv4, unicast and provided
        # in correct CIDR format. In case any requirement is violated the program cannot continue
        if args.peer_subnet:
            if type(args.peer_subnet) is not str:
                raise TypeError
            try:
                prefix = netaddr.IPNetwork(args.peer_subnet, version=4)
            except ValueError as e:
                raise ValueError("peer_subnet:", e.data)
            except netaddr.AddrFormatError as e:
                raise ValueError("peer_subnet: Address format error")
            else:
                if not prefix.is_unicast():
                    raise ValueError("peer_subnet: Non-unicast address")
                if prefix.prefixlen == 32:
                    raise ValueError("peer_subnet: Host address provided")
                self.peer_subnet = args.peer_subnet
            self.update_peer = True
