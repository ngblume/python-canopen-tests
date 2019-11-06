#!/usr/bin/env python
# coding: utf-8

import canopen
import can
import time
import logging
import os
import teststand_canopen

# EDS Path
EDS_PATH = os.path.join(os.path.dirname(__file__), '../00_EDS/SimNode/SimNode.eds')

# ==================================================================
# Create simulation network

# Create network_sim = network used to CREATE simulated nodes
network_sim = canopen.Network()
# Connect network_sim to same CAN bus (but may different channel !!)
# network_sim.connect(channel='can0', bustype='socketcan', bitrate=250000)
network_sim.connect(bustype='pcan', channel='PCAN_USBBUS2', bitrate=250000)
# Create simulated nodes (via network_sim) > called "local"
localSimNode_0x05 = network_sim.create_node(0x05, EDS_PATH)
# Set Index 0x1000-Subindex 0x00, which is scanned by scanner.search()
localSimNode_0x05.sdo[0x1000].raw = 0x000000AA
# Set "Manufacturer Device Name" (index via EDS file), which is later readback
localSimNode_0x05.sdo['Manufacturer Device Name'].raw = 'Device-Node 0x05'

# ==================================================================
# Create interface to the CANopen network (i.e. from TestStand)

# Instantiate class teststand_canopen
# interface = teststand_canopen.teststand_canopen(use_sep_bus_object=False, adapter='socketcan', channel='can0', bitrate=250000)
interface = teststand_canopen.teststand_canopen(use_sep_bus_object=True, adapter='pcan', channel='PCAN_USBBUS1', bitrate=250000)

# add remote node = 0x05 to network
remote_node_0x05 = interface.AddNode(0x05, EDS_PATH) # needs to be node 0x05, since that is the NodeID used for the simulated node

# Heartbeat and similar tests
# ==================================================================
print('Testing stuff with heartbeat > see CAN log, i.e. WireShark')
# Set nodes to different states for both nodes with different timing
localSimNode_0x05.nmt.state = 'INITIALISING'
# When node transistions from INITIALIZING to PRE-OPERATIONAL, heartbeat will start automatically with current value of 0x1017
localSimNode_0x05.nmt.state = 'PRE-OPERATIONAL'
time.sleep(5)
localSimNode_0x05.nmt.start_heartbeat(1000)
time.sleep(5)
localSimNode_0x05.nmt.state = 'OPERATIONAL'

# ==================================================================
# Use scanner to find active nodes
found_nodes = interface.Scanner()
print('Found Nodes: ', found_nodes)

# ==================================================================

# SDO Upload - Expedited Transfer - WITH RETURNED OBJECT
device_type_direct_node_0x05 = remote_node_0x05.sdo[0x1000].raw
print('Device Type on Node 0x05 - with returned object: ', '0x%0*X' % (8,device_type_direct_node_0x05))

# SDO Upload - Expedited Transfer - WITH NODE ID
device_type_id_node_0x05 = interface.SDO_Upload(node_id=0x05, mode='expedited', index=0x1000, subindex=0x00, timeout=2.0)
# Data is Bytes and needs to be converted an integer (little endian)
device_type_id_node_0x05 = int.from_bytes(device_type_id_node_0x05, byteorder='little', signed=False)
print('Device Type on Node 0x05 - with node_id : ', '0x%0*X' % (8,device_type_id_node_0x05))

# ==================================================================

# SDO Upload - Segmented Transfer - WITH RETURNED OBJECT
manufacturer_device_name_direct_node_0x05 = remote_node_0x05.sdo['Manufacturer Device Name'].data
print('Manufacturer Device Name on Node 0x05 - with returned object: ', manufacturer_device_name_direct_node_0x05)

# SDO Upload - Segmented Transfer - WITH NODE ID
manufacturer_device_name_id_node_0x05 = interface.SDO_Upload(node_id=0x05, mode='segmented', index=0x1008, subindex=0x00, timeout=2.0)
print('Manufacturer Device Name on Node 0x05 - with node_id: ', manufacturer_device_name_id_node_0x05)

# ==================================================================

# SDO Download - Expedited Transfer - WITH RETURNED OBJECT - followed by read-back
remote_node_0x05.sdo[0x1000].raw = 0x000010AA
time.sleep(0.2) # sleep 0.2 s for change to take effect - necessary ??
device_type_direct_node_0x05 = remote_node_0x05.sdo[0x1000].raw
print('Device Type on Node 0x05 - with returned object: ', '0x%0*X' % (8,device_type_direct_node_0x05))

# SDO Download - Expedited Transfer - WITH NODE ID - followed by read-back
data_to_send = 0x000010CC
data_to_send = data_to_send.to_bytes(4, byteorder="little", signed=False)
interface.SDO_Download(node_id=0x05, mode='expedited', index=0x1000, subindex=0x00, data=data_to_send, timeout=2.0)
time.sleep(0.2) # sleep 0.2 s for change to take effect - necessary ??
device_type_id_node_0x05 = interface.SDO_Upload(node_id=0x05, mode='expedited', index=0x1000, subindex=0x00, timeout=2.0)
# Data is Bytes and needs to be converted an integer (little endian)
device_type_id_node_0x05 = int.from_bytes(device_type_id_node_0x05, byteorder='little', signed=False)
print('Device Type on Node 0x05 - with node_id : ', '0x%0*X' % (8,device_type_id_node_0x05))

# ==================================================================

# SDO Download - Segmented Transfer - WITH RETURNED OBJECT - followed by read-back
remote_node_0x05.sdo['Manufacturer Device Name'].raw = 'embeX Node - Object'
time.sleep(0.2) # sleep 0.2 s for change to take effect - necessary ??
manufacturer_device_name_direct_node_0x05 = remote_node_0x05.sdo['Manufacturer Device Name'].data
print('Manufacturer Device Name on Node 0x05 - with returned object: ', manufacturer_device_name_direct_node_0x05)

# SDO Download - Expedited Transfer - WITH NODE ID - followed by read-back
data_to_send = 'embeX Node - ID'
data_to_send = data_to_send.encode('utf-8')
interface.SDO_Download(node_id=0x05, mode='segmented', index=0x1008, subindex=0x00, data=data_to_send, timeout=2.0)
time.sleep(0.2) # sleep 0.2 s for change to take effect - necessary ??
manufacturer_device_name_id_node_0x05 = interface.SDO_Upload(node_id=0x05, mode='segmented', index=0x1008, subindex=0x00, timeout=2.0)
print('Manufacturer Device Name on Node 0x05 - with node_id: ', manufacturer_device_name_id_node_0x05)

# ==================================================================

# SDO Upload - Expedited Transfer - WITH RETURNED OBJECT
device_type_direct_node_0x05 = remote_node_0x05.sdo[0x1000].raw
print('Device Type on Node 0x05 - with returned object: ', '0x%0*X' % (8,device_type_direct_node_0x05))

# SDO Upload - Expedited Transfer - WITH NODE ID
device_type_id_node_0x05 = interface.SDO_Upload(node_id=0x05, mode='expedited', index=0x1000, subindex=0x00, timeout=2.0)
# Data is Bytes and needs to be converted an integer (little endian)
device_type_id_node_0x05 = int.from_bytes(device_type_id_node_0x05, byteorder='little', signed=False)
print('Device Type on Node 0x05 - with node_id : ', '0x%0*X' % (8,device_type_id_node_0x05))

# ==================================================================

# Disconnect from network
interface.Disconnect

time.sleep(3)

# Destroy class instance
del interface

# ==================================================================

# Disconnect sim network
network_sim.disconnect()