#!/usr/bin/env python
# coding: utf-8

import canopen
import can
import time
import logging
import os

# =====================================================================================================================================
EDS_PATH = os.path.join(os.path.dirname(__file__), '../00_EDS/SimNode/SimNode.eds')

# Set if existing bus should be used
USE_EXISTING_BUS = True

# Set logging level
# logging.basicConfig(level=logging.DEBUG)

# =====================================================================================================================================
# Define simple callbackfunction for receiving message of specific ID
def _recv_callback(can_id, data, timestamp):
    print('CAN-ID: ', hex(can_id), ' - Data: ', data, '- Timestamp: ', timestamp)

# =====================================================================================================================================
if (USE_EXISTING_BUS == True):
    # Create bus (using SocketCAN, can0 and a bit rate of 250 kB/s)
    # can_bus = can.interface.Bus(bustype='socketcan', channel='can0', bitrate=250000)
    can_bus = can.interface.Bus(bustype='pcan', channel='PCAN_USBBUS1', bitrate=250000)

# =====================================================================================================================================
# Create network_real
network_real = canopen.Network()

if (USE_EXISTING_BUS == True):
    # Assign network to previoulyly created bus
    network_real.bus = can_bus
else:
    # Connect network_real to specific CAN bus 
    # network_real.connect(channel='can0', bustype='socketcan', bitrate=250000)
    network_real.connect(channel='PCAN_USBBUS1', bustype='pcan', bitrate=250000)

# Add simulated note to network_real
remoteSimNode_0x05 = network_real.add_node(0x05, EDS_PATH)
remoteSimNode_0x10 = network_real.add_node(0x10, EDS_PATH)

# =====================================================================================================================================
# Create network_sim = network used to CREATE simulated nodes
network_sim = canopen.Network()

if (USE_EXISTING_BUS == True):
    # Assign network to bus
    network_sim.bus = can_bus
else:
    # Connect network_sim to same CAN bus
    # network_sim.connect(channel='can0', bustype='socketcan')
    network_sim.connect(channel='PCAN_USBBUS1', bustype='pcan', bitrate=250000)

# Create simulated nodes (via network_sim) > called "local"
localSimNode_0x05 = network_sim.create_node(0x05, EDS_PATH)
localSimNode_0x10 = network_sim.create_node(0x10, EDS_PATH)

# =====================================================================================================================================
if (USE_EXISTING_BUS == True):
    # Add network listeners to created bus and start the notifier
    notifier = can.Notifier(can_bus, [can.Printer()] + network_real.listeners + network_real.listeners, 0.5)
    # Add notifier from canopen to notifers of bus
    # can.Notifier.add_listener(listener for listener in network_real.listeners)
    # can.Notifier.add_listener(listener for listener in network_sim.listeners)

# =====================================================================================================================================
# Set Index 0x1000-Subindex 0x00, which is scanned by scanner.search()
localSimNode_0x05.sdo[0x1000].raw = 0x000000AA
# Instead of setting the value, we will check for the default value 
# localSimNode_0x10.sdo[0x1000].raw = 0x000000BB

# Set "Manufacturer Device Name" (index via EDS file), which is later readback
localSimNode_0x05.sdo["Manufacturer Device Name"].raw = "Device-Node 0x05"
localSimNode_0x10.sdo["Manufacturer Device Name"].raw = "Device-Node 0x10"

# =====================================================================================================================================
print('Testing stuff with heartbeat > see CAN log, i.e. WireShark')
# Set nodes to different states for both nodes with different timing
localSimNode_0x05.nmt.state = 'INITIALISING'
# When node transistions from INITIALIZING to PRE-OPERATIONAL, heartbeat will start automatically with current value of 0x1017
localSimNode_0x05.nmt.state = 'PRE-OPERATIONAL'
time.sleep(5)
localSimNode_0x05.nmt.start_heartbeat(1000)
time.sleep(5)
localSimNode_0x05.nmt.state = 'OPERATIONAL'

localSimNode_0x10.nmt.state = 'INITIALISING'
# When node transistions from INITIALIZING to PRE-OPERATIONAL, heartbeat will start automatically with current value of 0x1017
localSimNode_0x10.nmt.state = 'PRE-OPERATIONAL'
time.sleep(5)
localSimNode_0x10.nmt.start_heartbeat(5000)
time.sleep(10)
localSimNode_0x10.nmt.state = 'OPERATIONAL'

# =====================================================================================================================================
# Scan network with scanner via Index 0x1000 Subindex 0x00
network_real.scanner.search()
# Wait for nodes to respond
time.sleep(1)
for node_id in network_real.scanner.nodes:
    print('Found node: ', hex(node_id))

# =====================================================================================================================================
time.sleep(1)
# Set SDO timeout longer (as an example)
remoteSimNode_0x05.sdo.RESPONSE_TIMEOUT = 2.0
remoteSimNode_0x10.sdo.RESPONSE_TIMEOUT = 2.0
# SDO upload via expedited transfer
device_type_node_0x05 = remoteSimNode_0x05.sdo[0x1000].raw
device_type_node_0x10 = remoteSimNode_0x10.sdo[0x1000].raw
# Print for debugging
print('Device Type on Node 0x05: ', '0x%0*X' % (8,device_type_node_0x05))
print('Device Type on Node 0x10: ',  '0x%0*X' % (8,device_type_node_0x10))

# =====================================================================================================================================
time.sleep(1)
# SDO upload via segmented transfer
device_name_node_0x05 = remoteSimNode_0x05.sdo["Manufacturer Device Name"].data
device_name_node_0x10 = remoteSimNode_0x10.sdo["Manufacturer Device Name"].data
# Print for debugging
print('Manufacturer Device Name on Node 0x05: ', device_name_node_0x05)
print('Manufacturer Device Name on Node 0x10: ', device_name_node_0x10)

# =====================================================================================================================================
# Test for BLOCK transfer ONLY possible with real node, since LocalNodes SDO server currently do not support BLOCK download
""" 
time.sleep(1)
# Download a long string via BLOCK transfer to the node via file-like access
data_0x05 = b'A really really long string on node 0x05...'
# Open file-like access with options: writing, binary (string is converted to binary before transmitting)
fp = remoteSimNode_0x05.sdo['FirmwareString'].open('wb', size=len(data_0x05), block_transfer=True)
fp.write(data_0x05)
fp.close()

time.sleep(1)
# Download a long string via BLOCK transfer to the node via file-like access
data_0x10 = b'A really really long string on node 0x10...'
# Open file-like access with options: writing, binary (string is converted to binary before transmitting)
fp = remoteSimNode_0x10.sdo['FirmwareString'].open('wb', size=len(data_0x10), block_transfer=True)
fp.write(data_0x10)
fp.close()

time.sleep(1)
# Upload a long string via BLOCK transfer from the node via file-like access
fp = remoteSimNode_0x05.sdo['FirmwareString'].open('r', block_transfer=True)
readback_data_0x05 = fp.read()
fp.close()
print('Firmware String on Node 0x05: ', readback_data_0x05)

time.sleep(1)
# Upload a long string via BLOCK transfer from the node via file-like access
fp = remoteSimNode_0x10.sdo['FirmwareString'].open('r', block_transfer=True)
readback_data_0x10 = fp.read()
fp.close()
print('Firmware String on Node 0x10: ', readback_data_0x10) 
"""

# =====================================================================================================================================
time.sleep(1)
# Read errors from node objects (complete objects)
active_objects_node_0x05 = remoteSimNode_0x05.emcy.active
active_objects_node_0x10 = remoteSimNode_0x10.emcy.active
# Print for debugging
print('Active EMCYs for Node 0x05: ', active_objects_node_0x05)
print('Active EMCYs for Node 0x10: ', active_objects_node_0x10)
# Trigger one error per node
print('Trigger one EMCYs per node and wait 3 sec...')
localSimNode_0x05.emcy.send(0x3001, register=4, data=b"Under")
localSimNode_0x10.emcy.send(0x1001, register=1, data=b"MEGAA")
time.sleep(3)
# Read errors from node objects (complete objects)
active_objects_node_0x05 = remoteSimNode_0x05.emcy.active
active_objects_node_0x10 = remoteSimNode_0x10.emcy.active
# Print for debugging
print('Active EMCYs for Node 0x05: ', active_objects_node_0x05)
print('Active EMCYs for Node 0x10: ', active_objects_node_0x10)
time.sleep(1)
# Reset error per node
print('Reset EMCYs per node and wait 3 sec...')
localSimNode_0x05.emcy.reset(register=4, data=b"CLEAR")
localSimNode_0x10.emcy.reset(register=1, data=b"CLEAR")
time.sleep(3)
# Read errors from node objects (complete objects)
active_objects_node_0x05 = remoteSimNode_0x05.emcy.active
active_objects_node_0x10 = remoteSimNode_0x10.emcy.active
# Print for debugging
print('Active EMCYs for Node 0x05: ', active_objects_node_0x05)
print('Active EMCYs for Node 0x10: ', active_objects_node_0x10)
# Read error log from node objects (complete objects)
log_objects_node_0x05 = remoteSimNode_0x05.emcy.log
log_objects_node_0x10 = remoteSimNode_0x10.emcy.log
# Print for debugging
print('EMCYs LOG for Node 0x05: ', log_objects_node_0x05)
print('EMCYs LOG for Node 0x10: ', log_objects_node_0x10)
# More print for debugging
print('EMCYs LOG for Node 0x05 (extended):')
for emcy in log_objects_node_0x05:
    print(emcy)
print('EMCYs LOG for Node 0x10 (extended):')
for emcy in log_objects_node_0x10:
    print(emcy)
# Reset logs for node 0x10 in python-canopen
remoteSimNode_0x10.emcy.reset()
# Read error log from node objects (complete objects)
log_objects_node_0x05 = remoteSimNode_0x05.emcy.log
log_objects_node_0x10 = remoteSimNode_0x10.emcy.log
# Print for debugging
print('EMCYs LOG for Node 0x05: ', log_objects_node_0x05)
print('EMCYs LOG for Node 0x10: ', log_objects_node_0x10)

# =====================================================================================================================================
time.sleep(1)
# Directly send messages
# Standard ID range
network_real.send_message(0x1FF, [0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF])
# Extended ID range
network_real.send_message(0x1FFFF, [0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF])

# =====================================================================================================================================
time.sleep(1)
# Subscribe to CAN ID 0x10A via callback
network_real.subscribe(0x10A, _recv_callback)
print('Subscribe to CAN ID 0x10A with callback...')
print('Subscription active for next 15 seconds...')
# Wait for callback to be triggered by sending msg from different system on bus
time.sleep(15)

# Unsubscribe from CAN ID 0x10A with identical callback (other callbacks will not be removed)
network_real.unsubscribe(0x10A, _recv_callback)
print('Unsubscribed...')

# Subscribe to CAN ID 0x10AFF via callback
network_real.subscribe(0x10AFF, _recv_callback)
print('Subscribe to CAN ID 0x10AFF with callback...')
print('Subscription active for next 15 seconds...')
# Wait for callback to be triggered by sending msg from different system on bus
time.sleep(15)

# Unsubscribe from CAN ID 0x10A with identical callback (other callbacks will not be removed)
network_real.unsubscribe(0x10AFF, _recv_callback)
print('Unsubscribed...')

# =====================================================================================================================================
time.sleep(20)
# Disconnect networks from CAN bus
network_real.disconnect()
network_sim.disconnect()