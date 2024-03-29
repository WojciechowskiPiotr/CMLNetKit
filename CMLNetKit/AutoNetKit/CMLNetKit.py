# -*- coding: utf-8 -*-
# (c) 2020-2023 Piotr Wojciechowski <piotr@it-playground.pl>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import netaddr
import yaml
from ciscoconfparse import CiscoConfParse
from virl2_client import ClientLibrary
from prettytable import PrettyTable


class CMLNetKit(object):
    """
    Initializes a CMLNetKit instance. This class is used to perform all the operations on CML2 lab.

    :param cml_options: Configuration stored in CMLNetKitConfig class.
    :type cml_options: CMLNetKitConfig class
    """

    lab_conf = None
    lab_handler = None
    _cmlnetkitconfig = None

    lab_conf_changed = False

    # Some static definitions
    _node_types = ['iosv', 'csr1000v', 'iosxrv', 'iosxrv9000', 'nxosv', 'nxosv9000', 'cat8000v']
    _node_iosv_fn = 'update_node_loopback_conf_iosv'
    _node_csr1000v_fn = 'update_node_loopback_conf_csr1000v'
    _node_types_fn = {}

    _node_management_interface_name = {'iosv': 'GigabitEthernet0/0',
                                       'csr1000v': 'GigabitEthernet1',
                                       'iosxrv': 'MgmtEth0/0/CPU0/0',
                                       'iosxrv9000': 'MgmtEth0/RP0/CPU0/0',
                                       'nxosv': 'mgmt0',
                                       'nxosv9000': 'mgmt0',
                                       'iosvl2': 'GigabitEthernet0/0',
                                       'asav': 'Management0/0',
                                       'cat8000v': 'GigabitEthernet1',
                                       }

    _node_types_supported = ['iosv', 'csr1000v', 'iosxrv', 'iosxrv9000', 'nxosv', 'nxosv9000', 'asav', 'cat8000v']
    _node_types_ignored = ['external_connector', 'iosvl2']

    def __init__(self, cml_options):
        super(CMLNetKit, self).__init__()

        self._cmlnetkitconfig = cml_options

        # Define functions to call for particular device type identified by node_definition key in the node
        # configuration downloaded from CML2 server. In some cases, we will call the dummy method because the proper
        # method is not yet implemented. In other cases, the same method applies to more than one node type.
        self._node_types_fn = {'update_node_loopback_conf_iosv': self.update_node_loopback_conf_iosv,
                               'update_node_loopback_conf_csr1000v': self.update_node_loopback_conf_iosv,
                               'update_node_loopback_conf_iosxrv': self.update_node_loopback_conf_iosxrv,
                               'update_node_loopback_conf_iosxrv9000': self.update_node_loopback_conf_iosxrv,
                               'update_node_loopback_conf_nxosv': self.update_node_loopback_conf_iosv,
                               'update_node_loopback_conf_nxosv9000': self.update_node_loopback_conf_iosv,
                               'update_node_loopback_conf_iosvl2': self.update_node_loopback_conf_iosv,
                               'update_node_loopback_conf_asav': self.dummy,
                               'update_node_loopback_conf_cat8000v': self.update_node_loopback_conf_iosv,
                               'update_node_loopback_conf_external_connector': self.dummy,
                               'update_node_management_conf_iosv': self.update_node_management_conf_iosv,
                               'update_node_management_conf_csr1000v': self.update_node_management_conf_csr1000v,
                               'update_node_management_conf_iosxrv': self.update_node_management_conf_iosxrv,
                               'update_node_management_conf_iosxrv9000': self.update_node_management_conf_iosxrv9000,
                               'update_node_management_conf_nxosv': self.update_node_management_conf_nxosv,
                               'update_node_management_conf_nxosv9000': self.update_node_management_conf_nxosv,
                               'update_node_management_conf_iosvl2': self.update_node_management_conf_iosvl2,
                               'update_node_management_conf_asav': self.update_node_management_conf_asav,
                               'update_node_management_conf_ccat8000v': self.update_node_management_conf_csr1000v,
                               'update_node_management_conf_external_connector': self.dummy,
                               'update_node_peer_interface_conf_iosv': self.update_node_interface_address_iosv,
                               'update_node_peer_interface_conf_csr1000v': self.update_node_interface_address_iosv,
                               'update_node_peer_interface_conf_iosxrv': self.update_node_interface_address_iosxrv,
                               'update_node_peer_interface_conf_iosxrv9000': self.update_node_interface_address_iosxrv,
                               'update_node_peer_interface_conf_asav': self.update_node_interface_address_iosv,
                               'update_node_peer_interface_conf_nxosv': self.update_node_interface_address_iosv,
                               'update_node_peer_interface_conf_nxosv9000': self.update_node_interface_address_iosv,
                               'update_node_peer_interface_conf_cat8000v': self.update_node_interface_address_iosv,
                               }

        if self._cmlnetkitconfig.list_labs:
            self.print_labs()
            exit(0)

        if self._cmlnetkitconfig.lab_id is None:
            self.print_labs()
            exit(0)

        self.lab_download()

        if self._cmlnetkitconfig.list_ips:
            self.print_lab_ip_addresses()
            exit(0)

        self.update_devices_confs()

        if self.lab_conf_changed is True:
            self.lab_upload()
        else:
            print("Lab configuration unchanged")

    def dummy(self, *argv):
        """
        This dummy method gets all the arguments and does nothing. Required for future methods implementations
        when need to call variable name function.

        :param argv:
        """
        pass

    def lab_download(self):
        """
        Imports an existing topology from a CML2 server. Downloaded configuration is stored in self.lab_conf class
        variable and parsed as YAML object

        :raises TypeError: if no lab_id is provided
        :raises requests.exceptions.HTTPError: if there was a transport error
        """

        cl = ClientLibrary(url="https://" + self._cmlnetkitconfig.host, username=self._cmlnetkitconfig.username,
                           password=self._cmlnetkitconfig.password,
                           ssl_verify=self._cmlnetkitconfig.ssl_verify)
        cl.is_system_ready(wait=True)
        try:
            self.lab_handler = cl.join_existing_lab(self._cmlnetkitconfig.lab_id)
            self.lab_conf = yaml.safe_load(self.lab_handler.download())
        except TypeError:
            print("TypeError: No lab_id provided. Use the -l option to provide the lab_id")

    def lab_upload(self):
        """
        Upload topology from the self.lab_conf class variable to CML2 server as a new lab, except if
        'dry run' mode is active.

        :raises requests.exceptions.HTTPError: if there was a transport error
        """
        if self._cmlnetkitconfig.dry_run is True:
            print("Dry Run mode: No changes applied to CML2 server")
            return

        cl = ClientLibrary(url="https://" + self._cmlnetkitconfig.host, username=self._cmlnetkitconfig.username,
                           password=self._cmlnetkitconfig.password,
                           ssl_verify=self._cmlnetkitconfig.ssl_verify)
        cl.is_system_ready(wait=True)
        self.lab_conf = cl.import_lab(topology=yaml.dump(self.lab_conf), title=self.lab_conf["lab"]["title"])

    def update_bridge(self):
        """
        Update the configuration of the "External Connection" objects to "bridge0" value. It is done by processing
        the lab configuration YAML object in self.lab_conf class variable
        """

        for nodenum, nodedef in enumerate(self.lab_conf["nodes"]):
            if nodedef.get("node_definition") == 'external_connector' and nodedef.get("configuration") != 'bridge0':
                self.lab_conf["nodes"][nodenum]["configuration"] = 'bridge0'
                self.lab_conf_changed = True

    def _get_node_index_by_label(self, node_name):
        """
        Search for the node in nodes definitions by the label and return the index on the list when found

        :param node_name: Node name
        :type: node_name: str
        :returns: Array index for the node
        :rtype: Integer
        """
        for nodenum, nodedef in enumerate(self.lab_conf["nodes"]):
            if nodedef.get("label") == node_name:
                return nodenum

    def _get_node_index_by_id(self, node_id):
        """
        Search for the node in nodes definitions by the id and return the index on the list when found

        :param node_id: Node name
        :type: node_id: str
        :returns: Array index for the node
        :rtype: Integer
        """
        for nodenum, nodedef in enumerate(self.lab_conf["nodes"]):
            if nodedef.get("id") == node_id:
                return nodenum

    def _get_node_label_by_id(self, node_id):
        """
        Search for the node in nodes definitions by the id and return the name of node when found

        :param node_id: Node name
        :type: node_id: str
        :returns: Array index for the node
        :rtype: String
        """
        for nodenum, nodedef in enumerate(self.lab_conf["nodes"]):
            if nodedef.get("id") == node_id:
                return nodedef.get("label")

    def _get_interface_name_by_id(self, node_id, iface_id):
        """
        Search for the interface in nodes definitions by the id and return the inteface configuration id when found

        :param node_id: Node name
        :type: node_id: str
        :param iface_id: Interface id
        :type: iface_id: str
        :returns: Interface name
        :rtype: str
        """
        for ifnum, ifdef in enumerate(self.lab_conf['nodes'][node_id]['interfaces']):
            if ifdef.get("id") == iface_id:
                return ifdef['label']

    def _get_node_config(self, node_index):
        """
        Read startup node configuration from lab configuration

        :param node_index: Node index in the configuration list
        :type node_index: int
        :return: Specific node configuration extracted from lab configuration
        :rtype: str
        """
        return self.lab_conf["nodes"][node_index]["configuration"]

    def _get_node_type(self, node_index):
        """
        Read the node type stored as node_definition key in lab configuration for specified node

        :param node_index: Node index in the configuration list
        :type node_index: int
        :return: Node type stored in node_definition
        :rtype: str
        """
        return self.lab_conf["nodes"][node_index]["node_definition"]

    def _set_node_config(self, node_index, node_config):
        """
        Replaces the node startup configuration for specific node in lab configuration

        :param node_index: Node index in the configuration list
        :type node_index: int
        :param node_config: Node configuration
        :type node_config: str
        """
        self.lab_conf["nodes"][node_index]["configuration"] = node_config

    def _iface_ip_addr_defined(self, iface_conf=None):
        """
        Checks if IP address is defined in the provided interface configuration

        :param iface_conf: List of interface configuration lines
        :type iface_conf: list
        :return: False if IP address is not defined, otherwise return Tue
        :rtype: Bool
        """
        if iface_conf is None:
            return False
        for config_line in iface_conf:
            if "no ip address" in config_line:
                return False
            if "no ipv4 address" in config_line:
                return False
        return True

    def _get_iface_ip_addr(self, iface_conf=None):
        """
        Returns IP address defined in the provided interface configuration

        :param iface_conf: List of interface configuration lines
        :type iface_conf: list
        :return: IP address and netmask of interface or None if no IP address is defined
        :rtype: netaddr.IPNetwork or None
        """
        if not self._iface_ip_addr_defined(iface_conf):
            return None
        for config_line in iface_conf:
            if "ip address" in config_line:
                return netaddr.IPNetwork(config_line.lstrip().split(' ')[2] + '/' + config_line.lstrip().split(' ')[3])
            if "ipv4 address" in config_line:
                return netaddr.IPNetwork(config_line.lstrip().split(' ')[2] + '/' + config_line.lstrip().split(' ')[3])
        return None

    def print_labs(self):
        """
        Get list of labs from CML2 server and print it formatted on console.

        :raises requests.exceptions.HTTPError: if there was a transport error
        """

        cl = ClientLibrary(url="https://" + self._cmlnetkitconfig.host, username=self._cmlnetkitconfig.username,
                           password=self._cmlnetkitconfig.password,
                           ssl_verify=self._cmlnetkitconfig.ssl_verify)
        cl.is_system_ready(wait=True)
        labs = cl.all_labs()
        print('\nLab ID\tLab Title')
        for lab in labs:
            print(lab.id + '\t' + lab.title)

    def print_lab_ip_addresses(self):
        """
        For selected lab read the configuration file and print to the console information on al addressed
        """

        self.print_lab_ip_peer_addresses()
        self.print_lab_ip_loopback_addresses()
        self.print_lab_ip_management_addresses()

    def print_lab_ip_peer_addresses(self):
        """
        Print to the console information about IP addresses and link of L3 interfaces in the lab.
        """

        # For each link we need to store 6 values. We use List of Dictionaries for this. Each link is described by
        # following structure:
        # {
        #   DeviceA: String,
        #   DeviceB: String,
        #   InterfaceA: String,
        #   InterfaceB: String,
        #   IPAddressA: netaddr.IPNetwork,
        #   IPAddressB: netaddr.IPNetwork
        # }
        links_database = []

        try:
            for linknum, link in enumerate(self.lab_conf["links"]):
                # We need to ignore connections to 'external_connector' and 'iosvl2' objects and continue to the
                # next object on list
                if self._get_node_type(
                        self._get_node_index_by_id(link['n1'])) in self._node_types_ignored or self._get_node_type(
                    self._get_node_index_by_id(link['n2'])) in self._node_types_ignored:
                    continue

                link_record = {
                    'InterfaceA': self._get_interface_name_by_id(self._get_node_index_by_id(link["n1"]), link["i1"]),
                    'InterfaceB': self._get_interface_name_by_id(self._get_node_index_by_id(link["n2"]), link["i2"]),
                    'DeviceA': self._get_node_label_by_id(link["n1"]),
                    'DeviceB': self._get_node_label_by_id(link["n2"]),
                    'IPAddressA': None,
                    'IPAddressB': None,
                }

                if self._get_node_type(
                        self._get_node_index_by_id(link["n1"])) in self._node_types_supported:
                    node_config = self._get_node_config(self._get_node_index_by_id(link["n1"]))
                    node_parsed_config = CiscoConfParse(node_config.split('\n'))

                    if self._iface_ip_addr_defined(
                            node_parsed_config.find_children(
                                r'^interface\s' + self._get_interface_name_by_id(self._get_node_index_by_id(link["n1"]),
                                                                                 link["i1"]))):
                        link_record['IPAddressA'] = self._get_iface_ip_addr(
                            node_parsed_config.find_children(
                                r'^interface\s' + self._get_interface_name_by_id(self._get_node_index_by_id(link["n1"]),
                                                                                 link["i1"])))

                if self._get_node_type(
                        self._get_node_index_by_id(link["n2"])) in self._node_types_supported:
                    node_config = self._get_node_config(self._get_node_index_by_id(link["n2"]))
                    node_parsed_config = CiscoConfParse(node_config.split('\n'))
                    if self._iface_ip_addr_defined(
                            node_parsed_config.find_children(
                                r'^interface\s' + self._get_interface_name_by_id(self._get_node_index_by_id(link["n2"]),
                                                                                 link["i2"]))):
                        link_record['IPAddressB'] = self._get_iface_ip_addr(
                            node_parsed_config.find_children(
                                r'^interface\s' + self._get_interface_name_by_id(self._get_node_index_by_id(link["n2"]),
                                                                                 link["i2"])))

                links_database.append(link_record)
        except IndexError as e:
            raise IndexError("peer-range: Not enough IP addresses provided")

        TOutput = PrettyTable()
        TOutput.field_names = ['Device A', 'Interface A', 'IP Address A', 'Device B', 'Interface B', 'IP Address B']
        for r in links_database:
            TOutput.add_row(
                [r['DeviceA'], r['InterfaceA'], r['IPAddressA'], r['DeviceB'], r['InterfaceB'], r['IPAddressB']])
        print("\nL3 interfaces addressing")
        print(TOutput)

    def print_lab_ip_loopback_addresses(self):
        """
        Print to the console information about IP addresses assigned to loopback interfaces.
        """
        # For each link we need to store 2 values. We use List of Dictionaries for this. Each link is described by
        # following structure:
        # {
        #   Device: String,
        #   LoopbackIP: String
        # }
        TOutput = PrettyTable()
        TOutput.field_names = ['Device name', 'Loopback IP']

        for nodenum, nodedef in enumerate(self.lab_conf['nodes']):

            if self._get_node_type(nodenum) in self._node_types_supported:
                interface_record = {'Device': nodedef['label'], 'LoopbackIPAddress': None}

                node_config = self._get_node_config(nodenum)
                node_parsed_config = CiscoConfParse(node_config.split('\n'))

                if self._iface_ip_addr_defined(node_parsed_config.find_children(r'^interface\sLoopback0')):
                    interface_record['LoopbackIPAddress'] = self._get_iface_ip_addr(
                        node_parsed_config.find_children(r'^interface\sLoopback0'))
                else:
                    interface_record['LoopbackIPAddress'] = None
                TOutput.add_row([interface_record['Device'], interface_record['LoopbackIPAddress']])

        print("\nLoopback interfaces addressing")
        print(TOutput)

    def print_lab_ip_management_addresses(self):
        """
        Print to the console information about IP addresses assigned to management interfaces.
        """
        # For each link we need to store 2 values. We use List of Dictionaries for this. Each link is described by
        # following structure:
        # {
        #   Device: String,
        #   ManagementIP: String
        # }
        TOutput = PrettyTable()
        TOutput.field_names = ['Device name', 'Management IP']

        for nodenum, nodedef in enumerate(self.lab_conf['nodes']):

            if self._get_node_type(nodenum) in self._node_types_supported:
                interface_record = {'Device': nodedef['label'], 'ManagementIPAddress': None}

                node_config = self._get_node_config(nodenum)
                node_parsed_config = CiscoConfParse(node_config.split('\n'))

                if self._iface_ip_addr_defined(node_parsed_config.find_children(
                        r'^interface\s' + self._node_management_interface_name[self._get_node_type(nodenum)])):
                    interface_record['ManagementIPAddress'] = self._get_iface_ip_addr(
                        node_parsed_config.find_children(
                            r'^interface\s' + self._node_management_interface_name[self._get_node_type(nodenum)]))
                else:
                    interface_record['ManagementIPAddress'] = None
                TOutput.add_row([interface_record['Device'], interface_record['ManagementIPAddress']])

        print("\nManagement interfaces addressing")
        print(TOutput)

    def update_devices_confs(self):
        """
        Iterates over the node lists. For known node types where configuration can be updated
        it calls other methods
        """

        if self._cmlnetkitconfig.update_bridge is True:
            self.update_bridge()

        if self._cmlnetkitconfig.update_loopback is True:
            self.update_device_loopback_conf()

        if self._cmlnetkitconfig.update_mgmt is True:
            self.update_device_management_conf()

        if self._cmlnetkitconfig.update_peer is True:
            self.update_device_peer_interfaces_conf()

    def update_device_loopback_conf(self):
        """
        Updates the Loopback interfaces configuration for nodes in the lab topology.

        For each node it will call the platform specific method to update Loopback interface address
        from provided subnet using the next available address for each device.
        """
        ip = netaddr.IPNetwork(self._cmlnetkitconfig.loopback_subnet)

        try:
            for nodenum, nodedef in enumerate(self.lab_conf["nodes"]):
                # We find the method to call using the self._node_types_fm dictionary
                try:
                    node_config = self._get_node_config(self._get_node_index_by_label(nodedef.get("label")))
                    node_parsed_config = CiscoConfParse(node_config.split('\n'))

                    self._node_types_fn["update_node_loopback_conf_" + self._get_node_type(
                        self._get_node_index_by_label(nodedef.get("label")))](node_parsed_config,
                                                                              ip[nodenum + 1].__str__())

                    node_parsed_config.atomic()
                    node_new_config = '\n'.join([i for i in node_parsed_config.ioscfg[0:]])
                    self._set_node_config(self._get_node_index_by_label(nodedef.get("label")), node_new_config)
                    self.lab_conf_changed = True
                except TypeError as e:
                    raise TypeError(e)
                # No key found in self._node_types_fn
                except KeyError as e:
                    # For other than known and specified in self._node_types_fn node types do nothing just ignore
                    continue
                    # raise KeyError(e)
                # Exception from CiscoConfParse constructor
                except ValueError as e:
                    raise ValueError(e)

        except IndexError as e:
            raise IndexError("lo-subnet: Not enough loopback addresses provided")

    def update_device_management_conf(self):
        """
        Updates the management interfaces configuration for nodes in the lab topology.

        For each node it will call the platform specific method to update Loopback interface address
        from provided subnet using the next available address for each device.
        """
        try:
            for nodenum, nodedef in enumerate(self.lab_conf["nodes"]):
                try:
                    ip = netaddr.IPNetwork(self._cmlnetkitconfig.mgmt_range[nodenum])
                except netaddr.AddrFormatError as e:
                    raise ValueError("%s" % e)
                except IndexError as e:
                    raise IndexError("mgmt-range: Not enough management addresses provided")
                ip.prefixlen = self._cmlnetkitconfig.mgmt_prefixlen

                # We find the method to call using the self._node_types_fm dictionary
                try:
                    node_config = self._get_node_config(self._get_node_index_by_label(nodedef.get("label")))
                    node_parsed_config = CiscoConfParse(node_config.split('\n'))

                    self._node_types_fn["update_node_management_conf_" + self._get_node_type(
                        self._get_node_index_by_label(nodedef.get("label")))](node_parsed_config, ip.ip.__str__(),
                                                                              ip.netmask.__str__())

                    node_parsed_config.atomic()
                    node_new_config = '\n'.join([i for i in node_parsed_config.ioscfg[0:]])
                    self._set_node_config(self._get_node_index_by_label(nodedef.get("label")), node_new_config)
                    self.lab_conf_changed = True
                except TypeError as e:
                    raise TypeError(e)
                # No key found in self._node_types_fn
                except KeyError as e:
                    # For other than known and specified in self._node_types_fn node types do nothing just ignore
                    continue
                    # raise KeyError(e)
                # Exception from CiscoConfParse constructor
                except ValueError as e:
                    raise ValueError(e)

        except IndexError as e:
            raise IndexError("mgmt-range: Not enough management addresses provided")

    def update_device_peer_interfaces_conf(self):
        """
        Updates the addresses on interfaces if directly connected devices.
        """
        subnets = list(netaddr.IPNetwork(self._cmlnetkitconfig.peer_subnet).subnet(30))

        try:
            for linknum, link in enumerate(self.lab_conf["links"]):
                iface_a_name = self._get_interface_name_by_id(self._get_node_index_by_id(link["n1"]), link["i1"])
                iface_b_name = self._get_interface_name_by_id(self._get_node_index_by_id(link["n2"]), link["i2"])

                # We need to ignore connections to 'external_connector' and 'iosvl2' objects
                if self._get_node_type(
                        self._get_node_index_by_id(link['n1'])) in self._node_types_ignored or self._get_node_type(
                    self._get_node_index_by_id(link['n2'])) in self._node_types_ignored:
                    continue

                if self._get_node_type(
                        self._get_node_index_by_id(link["n1"])) in self._node_types_supported:
                    node_a_config = self._get_node_config(self._get_node_index_by_id(link["n1"]))
                    node_a_parsed_config = CiscoConfParse(node_a_config.split('\n'))

                    self._node_types_fn["update_node_peer_interface_conf_" + self._get_node_type(
                        self._get_node_index_by_id(link["n1"]))](node_a_parsed_config, iface_a_name,
                                                                 subnets[linknum][1].__str__(),
                                                                 subnets[linknum].netmask.__str__())

                    node_a_parsed_config.atomic()
                    node_a_new_config = '\n'.join([i for i in node_a_parsed_config.ioscfg[0:]])
                    self._set_node_config(self._get_node_index_by_id(link["n1"]), node_a_new_config)
                    self.lab_conf_changed = True

                if self._get_node_type(
                        self._get_node_index_by_id(link["n2"])) in self._node_types_supported:
                    node_b_config = self._get_node_config(self._get_node_index_by_id(link["n2"]))
                    node_b_parsed_config = CiscoConfParse(node_b_config.split('\n'))

                    self._node_types_fn["update_node_peer_interface_conf_" + self._get_node_type(
                        self._get_node_index_by_id(link["n2"]))](node_b_parsed_config, iface_b_name,
                                                                 subnets[linknum][2].__str__(),
                                                                 subnets[linknum].netmask.__str__())

                    node_b_parsed_config.atomic()
                    node_b_new_config = '\n'.join([i for i in node_b_parsed_config.ioscfg[0:]])
                    self._set_node_config(self._get_node_index_by_id(link["n2"]), node_b_new_config)
                    self.lab_conf_changed = True
        except IndexError as e:
            raise IndexError("peer-range: Not enough IP addresses provided")

    def update_node_loopback_conf_iosv(self, node_parsed_config=None, ip_addr=None):
        """
        Update the IP address, description and shutdown state configuration of Loopback interface
        if no IP address is assigned

        :param node_parsed_config: The parsed node configuration
        :type node_parsed_config: CiscoConfParse
        :param ip_addr: The IP address that will be assigned to Loopback interface of the device
        :type ip_addr: str
        """
        # Don't update the interface configuration if IP address is already set
        if self._iface_ip_addr_defined(node_parsed_config.find_children(r'^interface\sLoopback0')):
            return

        node_parsed_config.replace_children(r'^interface\sLoopback0', r'no ip address',
                                            r'ip address ' + ip_addr + ' 255.255.255.255')
        node_parsed_config.replace_children(r'^interface\sLoopback0', r'shutdown', r'no shutdown')
        node_parsed_config.replace_children(r'^interface\sLoopback0', r'description to',
                                            r'description Loopback interface')

    def update_node_loopback_conf_iosxrv(self, node_parsed_config=None, ip_addr=None):
        """
        Update the IP address, description and shutdown state configuration of Loopback interface
        if no IP address is assigned

        :param node_parsed_config: The parsed node configuration
        :type node_parsed_config: CiscoConfParse
        :param ip_addr: The IP address that will be assigned to Loopback interface of the device
        :type ip_addr: str
        """
        # Don't update the interface configuration if IP address is already set
        if self._iface_ip_addr_defined(node_parsed_config.find_children(r'^interface\sLoopback0')):
            return

        node_parsed_config.replace_children(r'^interface\sLoopback0', r'no ipv4 address',
                                            r'ipv4 address ' + ip_addr + ' 255.255.255.255')
        node_parsed_config.replace_children(r'^interface\sLoopback0', r'shutdown', r'no shutdown',
                                            excludespec=r'no shutdown')
        node_parsed_config.replace_children(r'^interface\sLoopback0', r'description to',
                                            r'description Loopback interface')

    def update_node_management_conf_iosv(self, node_parsed_config=None, ip_addr=None, ip_netmask=None):
        """
        Update the IP address, description and shutdown state configuration of GigabitEthernet0/0 interface
        if no IP address is assigned. There is no dedicated OOB Management interface so we take
        first one. If should be connected to "External Connection" object and common management subnet

        :param node_parsed_config: The parsed node configuration
        :type node_parsed_config: CiscoConfParse
        :param ip_addr: The IP address that will be assigned to te interface of the device and subnet mask
        :type ip_addr: str
        :param ip_netmask: The subnet mask in dot notation
        :type ip_netmask: str
        """
        # Don't update the interface configuration if IP address is already set
        if self._iface_ip_addr_defined(node_parsed_config.find_children(r'^interface\sGigabitEthernet0/0')):
            return

        node_parsed_config.replace_children(r'^interface\sGigabitEthernet0/0', r'no ip address',
                                            r'ip address ' + ip_addr + ' ' + ip_netmask)
        node_parsed_config.replace_children(r'^interface\sGigabitEthernet0/0', r'shutdown', r'no shutdown',
                                            excludespec=r'no shutdown')
        node_parsed_config.replace_children(r'^interface\sGigabitEthernet0/0', r'description to',
                                            r'description Management interface')

    def update_node_management_conf_csr1000v(self, node_parsed_config=None, ip_addr=None, ip_netmask=None):
        """
        Update the IP address, description and shutdown state configuration of GigabitEthernet0/0 interface
        if no IP address is assigned. There is no dedicated OOB Management interface so we take
        first one. If should be connected to "External Connection" object and common management subnet

        :param node_parsed_config: The parsed node configuration
        :type node_parsed_config: CiscoConfParse
        :param ip_addr: The IP address that will be assigned to te interface of the device and subnet mask
        :type ip_addr: str
        :param ip_netmask: The subnet mask in dot notation
        :type ip_netmask: str
        """
        # Don't update the interface configuration if IP address is already set
        if self._iface_ip_addr_defined(node_parsed_config.find_children(r'^interface\sGigabitEthernet1')):
            return

        node_parsed_config.replace_children(r'^interface\sGigabitEthernet1', r'no ip address',
                                            r'ip address ' + ip_addr + ' ' + ip_netmask)
        node_parsed_config.replace_children(r'^interface\sGigabitEthernet1', r'shutdown', r'no shutdown',
                                            excludespec=r'no shutdown')
        node_parsed_config.replace_children(r'^interface\sGigabitEthernet1', r'description to',
                                            r'description Management interface')

    def update_node_management_conf_iosxrv(self, node_parsed_config=None, ip_addr=None, ip_netmask=None):
        """
        Update the IP address, description and shutdown state configuration of MgmtEth0/0/CPU0/0 interface
        if no IP address is assigned. It should be connected to "External Connection" object and common
        management subnet.

        :param node_parsed_config: The parsed node configuration
        :type node_parsed_config: CiscoConfParse
        :param ip_addr: The IP address that will be assigned to te interface of the device and subnet mask
        :type ip_addr: str
        :param ip_netmask: The subnet mask in dot notation
        :type ip_netmask: str
        """
        # Don't update the interface configuration if IP address is already set
        if self._iface_ip_addr_defined(node_parsed_config.find_children(r'^interface\sMgmtEth0/0/CPU0/0')):
            return

        node_parsed_config.replace_children(r'^interface\sMgmtEth0/0/CPU0/0', r'no ipv4 address',
                                            r'ipv4 address ' + ip_addr + ' ' + ip_netmask)
        node_parsed_config.replace_children(r'^interface\sMgmtEth0/0/CPU0/0', r'shutdown', r'no shutdown',
                                            excludespec=r'no shutdown')
        node_parsed_config.replace_children(r'^interface\sMgmtEth0/0/CPU0/0', r'description to',
                                            r'description Management interface')

    def update_node_management_conf_iosxrv9000(self, node_parsed_config=None, ip_addr=None, ip_netmask=None):
        """
        Update the IP address, description and shutdown state configuration of MgmtEth0/0/CPU0/0 interface
        if no IP address is assigned. It should be connected to "External Connection" object and common
        management subnet.

        :param node_parsed_config: The parsed node configuration
        :type node_parsed_config: CiscoConfParse
        :param ip_addr: The IP address that will be assigned to te interface of the device and subnet mask
        :type ip_addr: str
        :param ip_netmask: The subnet mask in dot notation
        :type ip_netmask: str
        """
        # Don't update the interface configuration if IP address is already set
        if self._iface_ip_addr_defined(node_parsed_config.find_children(r'^interface\sMgmtEth0/RP0/CPU0/0')):
            return

        node_parsed_config.replace_children(r'^interface\sMgmtEth0/RP0/CPU0/0', r'no ipv4 address',
                                            r'ipv4 address ' + ip_addr + ' ' + ip_netmask)
        node_parsed_config.replace_children(r'^interface\sMgmtEth0/RP0/CPU0/0', r'shutdown', r'no shutdown',
                                            excludespec=r'no shutdown')
        node_parsed_config.replace_children(r'^interface\sMgmtEth0/RP0/CPU0/0', r'description to',
                                            r'description Management interface')

    def update_node_management_conf_nxosv(self, node_parsed_config=None, ip_addr=None, ip_netmask=None):
        """
        Update the IP address, description and shutdown state configuration of MgmtEth0/0/CPU0/0 interface
        if no IP address is assigned. It should be connected to "External Connection" object and common
        management subnet.

        :param node_parsed_config: The parsed node configuration
        :type node_parsed_config: CiscoConfParse
        :param ip_addr: The IP address that will be assigned to te interface of the device and subnet mask
        :type ip_addr: str
        :param ip_netmask: The subnet mask in dot notation
        :type ip_netmask: str
        """
        # Don't update the interface configuration if IP address is already set
        if self._iface_ip_addr_defined(node_parsed_config.find_children(r'^interface\smgmt0')):
            return

        node_parsed_config.replace_children(r'^interface\smgmt0', r'no ip address',
                                            r'ip address ' + ip_addr + ' ' + ip_netmask)
        node_parsed_config.replace_children(r'^interface\smgmt0', r'shutdown', r'no shutdown',
                                            excludespec=r'no shutdown')
        node_parsed_config.replace_children(r'^interface\smgmt0', r'description to',
                                            r'description Management interface')

    def update_node_management_conf_iosvl2(self, node_parsed_config=None, ip_addr=None, ip_netmask=None):
        """
        Update the IP address, description and shutdown state configuration of GigabitEthernet0/0 interface
        if no IP address is assigned. There is no dedicated OOB Management interface so we take
        first one. If should be connected to "External Connection" object and common management subnet

        :param node_parsed_config: The parsed node configuration
        :type node_parsed_config: CiscoConfParse
        :param ip_addr: The IP address that will be assigned to te interface of the device and subnet mask
        :type ip_addr: str
        :param ip_netmask: The subnet mask in dot notation
        :type ip_netmask: str
        """
        # Don't update the interface configuration if IP address is already set
        if self._iface_ip_addr_defined(node_parsed_config.find_children(r'^interface\sGigabitEthernet0/0')):
            return

        node_parsed_config.replace_children(r'^interface\sGigabitEthernet0/0', r'no ip address',
                                            r'ip address ' + ip_addr + ' ' + ip_netmask)
        node_parsed_config.replace_children(r'^interface\sGigabitEthernet0/0', r'shutdown', r'no shutdown',
                                            excludespec=r'no shutdown')
        node_parsed_config.replace_children(r'^interface\sGigabitEthernet0/0', r'switchport', r'no no switchport',
                                            excludespec=r'no switchport')
        node_parsed_config.replace_children(r'^interface\sGigabitEthernet0/0', r'description to',
                                            r'description Management interface')

    def update_node_management_conf_asav(self, node_parsed_config=None, ip_addr=None, ip_netmask=None):
        """
        Update the IP address, description and shutdown state configuration of GigabitEthernet0/0 interface
        if no IP address is assigned. There is no dedicated OOB Management interface so we take
        first one. If should be connected to "External Connection" object and common management subnet

        :param node_parsed_config: The parsed node configuration
        :type node_parsed_config: CiscoConfParse
        :param ip_addr: The IP address that will be assigned to te interface of the device and subnet mask
        :type ip_addr: str
        :param ip_netmask: The subnet mask in dot notation
        :type ip_netmask: str
        """
        # Don't update the interface configuration if IP address is already set
        if self._iface_ip_addr_defined(node_parsed_config.find_children(r'^interface\sManagement0/0')):
            return

        node_parsed_config.replace_children(r'^interface\sManagement0/0', r'no ip address',
                                            r'ip address ' + ip_addr + ' ' + ip_netmask)
        node_parsed_config.replace_children(r'^interface\sManagement0/0', r'shutdown', r'no shutdown',
                                            excludespec=r'no shutdown')
        node_parsed_config.replace_children(r'^interface\sManagement0/0', r'description to',
                                            r'description Management interface')

    def update_node_interface_address_iosv(self, node_parsed_config=None, iface_name=None, ip_addr=None,
                                           ip_netmask=None):
        """
        Update the IP address, description and shutdown state configuration of GigabitEthernet0/0 interface
        if no IP address is assigned. There is no dedicated OOB Management interface so we take
        first one. If should be connected to "External Connection" object and common management subnet

        :param node_parsed_config: The parsed node configuration
        :type node_parsed_config: CiscoConfParse
        :param iface_name: Name of the interface to be updated
        :type iface_name: str
        :param ip_addr: The IP address that will be assigned to te interface of the device and subnet mask
        :type ip_addr: str
        :param ip_netmask: The subnet mask in dot notation
        :type ip_netmask: str
        """
        # Don't update the interface configuration if IP address is already set
        if self._iface_ip_addr_defined(node_parsed_config.find_children(r'^interface\s' + iface_name)):
            return

        node_parsed_config.replace_children(r'^interface\s' + iface_name, r'no ip address',
                                            r'ip address ' + ip_addr + ' ' + ip_netmask)
        node_parsed_config.replace_children(r'^interface\s' + iface_name, r'shutdown', r'no shutdown',
                                            excludespec=r'no shutdown')

    def update_node_interface_address_iosxrv(self, node_parsed_config=None, iface_name=None, ip_addr=None,
                                             ip_netmask=None):
        """
        Update the IP address, description and shutdown state configuration of GigabitEthernet0/0 interface
        if no IP address is assigned. There is no dedicated OOB Management interface so we take
        first one. If should be connected to "External Connection" object and common management subnet

        :param node_parsed_config: The parsed node configuration
        :type node_parsed_config: CiscoConfParse
        :param iface_name: Name of the interface to be updated
        :type iface_name: str
        :param ip_addr: The IP address that will be assigned to te interface of the device and subnet mask
        :type ip_addr: str
        :param ip_netmask: The subnet mask in dot notation
        :type ip_netmask: str
        """
        # Don't update the interface configuration if IP address is already set
        if self._iface_ip_addr_defined(node_parsed_config.find_children(r'^interface\s' + iface_name)):
            return

        node_parsed_config.replace_children(r'^interface\s' + iface_name, r'no ipv4 address',
                                            r'ipv4 address ' + ip_addr + ' ' + ip_netmask)
        node_parsed_config.replace_children(r'^interface\s' + iface_name, r'shutdown', r'no shutdown',
                                            excludespec=r'no shutdown')
