#!/usr/bin/env python
# coding: utf-8

"""
This example scans nodes 1 to 127 by trying to perform an SDO operation
"""

import canopen
import time
import logging
import os

EDS_PATH = os.path.join(os.path.dirname(__file__), '../00_EDS/SimNode/SimNode.eds')

# Set logging level
# logging.basicConfig(level=logging.DEBUG)

# Create network_real
network_real = canopen.Network()

# Connect network_real to specific CAN bus
network_real.connect(channel='can0', bustype='socketcan')

# Add simulated note to network_real
remoteSimNode_0x05 = network_real.add_node(0x05, EDS_PATH)
remoteSimNode_0x10 = network_real.add_node(0x10, EDS_PATH)

# Create network_sim = network used to CREATE simulated nodes
network_sim = canopen.Network()

# Connect network_sim to same CAN bus
network_sim.connect(channel='can0', bustype='socketcan')

# Create simulated nodes (via network_sim) > called "local"
localSimNode_0x05 = network_sim.create_node(0x05, EDS_PATH)
localSimNode_0x10 = network_sim.create_node(0x10, EDS_PATH)

# Set Index 0x1000-Subindex 0x00, which is scanned by scanner.search()
localSimNode_0x05.sdo[0x1000].raw = 0x000000AA
# Instead of setting the value, we will check for the default value 
# localSimNode_0x10.sdo[0x1000].raw = 0x000000BB

# Set "Manufacturer Device Name" (index via EDS file), which is later readback
localSimNode_0x05.sdo["Manufacturer Device Name"].raw = "Device-Node 0x05"
localSimNode_0x10.sdo["Manufacturer Device Name"].raw = "Device-Node 0x10"

# Scan network with scanner via Index 0x1000 Subindex 0x00
network_real.scanner.search()
# Wait for nodes to respond
time.sleep(0.5)
for node_id in network_real.scanner.nodes:
    print("Found node %d!" % node_id)

# SDO upload via expedited transfer
device_type_node_0x05 = remoteSimNode_0x05.sdo[0x1000].raw
device_type_node_0x10 = remoteSimNode_0x10.sdo[0x1000].raw
# Print for debugging
print('Device Type on Node 0x05: ', '0x%0*X' % (8,device_type_node_0x05))
print('Device Type on Node 0x10: ',  '0x%0*X' % (8,device_type_node_0x10))

# SDO upload via segmented transfer
device_name_node_0x05 = remoteSimNode_0x05.sdo["Manufacturer Device Name"].data
device_name_node_0x10 = remoteSimNode_0x10.sdo["Manufacturer Device Name"].data
# Print for debugging
print('Manufacturer Device Name on Node 0x05: ', device_name_node_0x05)
print('Manufacturer Device Name on Node 0x10: ', device_name_node_0x10)

# Disconnect networks from CAN bus
network_real.disconnect()
network_sim.disconnect()