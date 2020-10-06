==============
CMLNetKit
==============

.. image:: http://img.shields.io/badge/license-GPLv3-blue.svg
   :target: https://www.gnu.org/copyleft/gpl.html
   :alt: License

.. contents::

.. _introduction:

What is CMLNetKit?
==================

CMLNetKit is a small application for device automatic pre-configuration for Cisco Modeling Labs 2.0

In Cisco VIRL the most valuable feature is AutoNetKit. It creates the initial configuration of simulated devices, including
the interface IP address, the loopback interfaces addressing, routing protocols, and many more. This feature pretty much does not
exist in Cisco Modeling Labs 2.0, aka. Cisco VIRL2 requiring a manual configuration of every essential feature. The
CMLNetKit brings some of the AutoNetKit features back to CML2.0

Usage
=====

The following options are required or optional


.. code::

    usage: cmlnetkit.py [-h] [-H HOST] [-l LAB_ID] [--list-labs] [--list-ips]
                        [-P PORT] [-u USERNAME] [-p PASSWORD]
                        [--no-ssl-verification] [--dry-run] [-b]
                        [--lo-subnet LOOPBACK_SUBNET]
                        [--mgmt-range MGMT_IP_LOW MGMT_IP_HIGH]
                        [--peer-subnet PEER_SUBNET]
                        [--mgmt-netmask MGMT_NETMASK | --mgmt-prefixlen MGMT_PREFIXLEN]

    optional arguments:
      -h, --help            show this help message and exit

    Connection options:
      -H HOST, --host HOST  CML2.0 host address
      -l LAB_ID, --lab LAB_ID
                            Lab ID
      --list-labs           List the ID of existing labs
      --list-ips            List the IP addresses configured on L3 links
      -P PORT, --port PORT  CML 2.0 API port (default 443)
      -u USERNAME, --username USERNAME
                            CML 2.0 API username (default "virl2")
      -p PASSWORD, --password PASSWORD
                            CML 2.0 API password (default "virl2")
      --no-ssl-verification
                            Disable the SSL certification verification on the CML2
                            server
      --dry-run             Don't apply any changes to CML2 server.

    Configuration changes:
      -b                    Changing all "External Connection" objects
                            configuration to "Bridge"
      --lo-subnet LOOPBACK_SUBNET
                            Subnet for the Loopback ip addresses assignment, must
                            be provided in format as subnet/mask. If mask not
                            provided default mask for subnet is used.If none
                            provided the default 10.0.0.0/24 is used. Loopback
                            addresses are always /32
      --mgmt-range MGMT_IP_LOW MGMT_IP_HIGH
                            Contiguous range of IP addresses must be provided. As
                            argument values provide first and last IP address of
                            the range
      --peer-subnet PEER_SUBNET
                            Subnet for the ip addresses assignment for direct
                            connections betweend devices,must be provided in
                            format as subnet/mask. If mask not provided the /24 is
                            used.Direct connections betweend devices are addressed
                            with /30 mask
      --mgmt-netmask MGMT_NETMASK
                            Subnet mask that needs to be assigned to management
                            interfaces IP addresses on devices. Mask must be
                            provided in standard netmask notation 255.255.255.0 If
                            neither -mgmt-netmask nor -mgmt-prefixlen is provided
                            then /24 prefixlen (mask of 255.255.255.0) is
                            assigned.
      --mgmt-prefixlen MGMT_PREFIXLEN
                            Subnet mask that needs to be assigned to management
                            interfaces IP addresses on devices. Prefixlen must be
                            provided as integer between 0 and 32. If neither
                            -mgmt-netmask nor -mgmt-prefixlen is provided then /24
                            prefixlen (mask of 255.255.255.0) is assigned.

.. _Pre-Requisites:

Pre-requisites
==============

CMLNetKit requires Python versions 3.5+. The OS should not
matter. It has been tested on Python version 3.7.7

The required Python libraries are defined in ``requirements.txt``


Features
========

The following features has already been deployed:
 * Reading and writing the lab configuration from API
 * Changing all ``External Connection`` objects types to ``Bridge``
 * Addressing Loopback interface
 * Addressing management interfaces
 * Addressing peer-to-peer interfaces

CMLNetKit does not modify the provided source lab topology, instead it creates new lab using the same title.

Management interfaces
---------------------

The dedicated management interfaces are not present on all node types. In this application the management interfaces
are statically defined as per below table. So if you request CMLNetKit to address the
management interfaces it will treat following interfaces as management. Usually those interfaces should be bridged into
the management network.

+------------+----------------------+
| Node type  | Management interface |
+============+======================+
| iosv       | GigabitEthernet0/0   |
+------------+----------------------+
| csr1000v   | GigabitEthernet1     |
+------------+----------------------+
| iosxrv     | MgmtEth0/0/CPU0/0    |
+------------+----------------------+
| iosxrv9000 | MgmtEth0/RP0/CPU0/0  |
+------------+----------------------+
| nxosv      | mgmt0                |
+------------+----------------------+
| nxosv9000  | mgmt0                |
+------------+----------------------+
| iosvl2     | GigabitEthernet0/0   |
+------------+----------------------+
| asav       | Management0/0        |
+------------+----------------------+


Usage examples
==============

First you need to list available labs on CML2 server
.. code::

    cmlnetkit.py -H cml.server.address --list-labs

To change the "External Connection" objects configuration to "bridge"
.. code::

    cmlnetkit.py -H cml.server.address -l abc123 -b

Addressing the Loopback interfaces

.. code::

    cmlnetkit.py -H cml.server.address -l abc123 -lo --lo-subnet 10.0.0.0/24

Addressing the management interfaces

.. code::

    cmlnetkit.py -H cml.server.address -labc123 -mgmt --mgmt-range 172.16.16.2 172.16.16.25 --mgmt-prefixlen 24

Addressing the direct connections between the simulation devices

.. code::

    cmlnetkit.py -H cml.server.address -l abc123 --peer-subnet 10.100.0.0/22

Everything altogether with SSL verification disabled

.. code::

    cmlnetkit.py -H cml.server.address -l abc123 --no-ssl-verification -lo --lo-subnet 10.0.0.0/24 -mgmt --mgmt-range 172.16.16.2 172.16.16.25 --mgmt-prefixlen 24 --peer-subnet 10.100.0.0/22

List IP addresses assigned to devices in initial configuration

.. code::

    cmlnetkit.py -H cml.server.address -l abc123 --list-ip
