#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    canopen_daemon

    A daemon, that can be reached via ZMQ and is part of a CANopen network
    allowing multiple concurrent process to access the CANopen network
    as well as allow continuous process (i.e. receiving CAN messages) to work,
    while the caller only communicates occasionally with the daemon.

    use-case:
    NI TestStand  <--->  LabVIEW  <--->  ZMQ  <--->  canopen_daemon  <--->  CANopen network
    
    Author: Niels Göran Blume
    Company: embeX GmbH, Freiburg im Breisgau, Germany
"""

# ================================================================================
import time
import logging
import os
import struct
import json

import canopen
import can

import zmq

# Print debug infos ??
DEBUG = False

# Use SIM-Network
SIM_NETWORK = True

# EDS Path - Used for SimNode only
SIM_EDS_PATH = os.path.join(os.path.dirname(__file__), '../20_EDS/SimNode/SimNode.eds')

# Variables
stop_daemon = False
nodes = {}
subscribe_msg_count = 0
subscribe_msg_id = 0
subscribe_msg_data = []
subscribe_msg_timestamp = 0
time_waited = 0

# ================================================================================
# Additional Functions

# Define simple callbackfunction for receiving message of specific ID
def _recv_callback(can_id, data, timestamp):
    global subscribe_msg_count, subscribe_msg_id, subscribe_msg_data, subscribe_msg_timestamp
    if DEBUG:
        print('CAN-ID: ', hex(can_id), ' - Data: ', data, '- Timestamp: ', timestamp)
    if subscribe_msg_count == 0:
        subscribe_msg_count = 1
        subscribe_msg_id = can_id
        subscribe_msg_data = list(data)
        subscribe_msg_timestamp = timestamp
    else:
        # other msgs than the first will be ignored, but still handled
        pass


# ================================================================================
# Init ZMQ
context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5555")

# ================================================================================
# Init CANopen

# Set logging level
# if DEBUG:
#     logging.basicConfig(level=logging.DEBUG)

# Create bus (using SocketCAN, can0 and a bit rate of 250 kB/s)
# can_bus = can.interface.Bus(bustype='socketcan', channel='can0', bitrate=250000)
can_bus = can.interface.Bus(bustype='pcan', channel='PCAN_USBBUS1', bitrate=250000)

# Create network
network = canopen.Network()

# Assign network to previoulyly created bus
network.bus = can_bus

# Set notifier
network.notifier = can.Notifier(network.bus, network.listeners, 1)

# ================================================================================
if SIM_NETWORK:
    # Create SimNode with NodeID = 0x03 for testing
    print('Setting up test environment with SimNode - node_id = 0x03 ...')
    # Create network_sim = network used to CREATE simulated nodes
    network_sim = canopen.Network()

    # Connect network_sim to same CAN bus (but may different channel !!)
    # network_sim.connect(channel='can0', bustype='socketcan', bitrate=250000)
    network_sim.connect(bustype='pcan', channel='PCAN_USBBUS2', bitrate=250000)

    # Create simulated nodes (via network_sim) > called "local"
    localSimNode_0x03 = network_sim.create_node(0x03, SIM_EDS_PATH)

    # Set Index 0x1000-Subindex 0x00, which is scanned by scanner.search()
    # Set in EDS file - localSimNode_0x03.sdo[0x1000].raw = 0x00000022

    # Set "Manufacturer Device Name" (index via EDS file), which is later readback
    # Set in EDS file - localSimNode_0x03.sdo['Manufacturer Device Name'].raw = 'SimNode-0x03'

    print('Transistion node to OPERATIONAL state ...')
    # Heartbeat and similar tests
    # Set nodes to different states for both nodes with different timing
    localSimNode_0x03.nmt.state = 'INITIALISING'
    time.sleep(1)

    # When node transistions from INITIALISING to PRE-OPERATIONAL, heartbeat will start automatically with current value of 0x1017
	localSimNode_0x03.sdo[0x1017].raw = 0x000005DC
    localSimNode_0x03.nmt.state = 'PRE-OPERATIONAL'
    time.sleep(1)

    # Transition node to OPERATIONAL
    localSimNode_0x03.nmt.state = 'OPERATIONAL'

    print('Test environment with SimNode ready ...')

    

# ================================================================================
# Main (will be left via a CMD)
print('CANopen - Daemon ready to receive messages ...')
keep_running = True
while stop_daemon == False:
    
    # ================================================================================
    #  Wait for next request from client
    message = socket.recv_string(encoding='utf-8')
    print("Received message: %s" % message)

    # Parse string as JSON
    message_dict = json.loads(message)

    # DEBUG Pretty print JSON
    if DEBUG:
        print(json.dumps(message_dict, indent = 4, sort_keys=True))
    
    if 'cmd' in message_dict:
        if DEBUG:
            print('Message contained CMD value: ', message_dict['cmd'], ' - executing command')
        cmd = message_dict.get('cmd', '')
        parameters = message_dict.get('parameters', None)
    else:
        if DEBUG:
            print('Message contained NO CMD value - ignoring message')
        cmd = ''
        parameters: None

    # Prepare reply (with data that makes not writing correct response data obvious)
    reply_cmd = 'err: no reply written for case'
    reply_parameters = {}

    # ===========================================================
    # Stop daemon
    if cmd == 'turn_off':
        # stop daemon
        stop_daemon = True
        reply_cmd = 'turn_off'

    # ===========================================================
    # Add node
    elif cmd == 'add_node':
        # Add remote node to CANopen network
        node_id = parameters.get('node_id', 0x00)
        EDS = parameters.get('EDS', '')
        EDS_PATH = os.path.join(os.path.dirname(__file__), '../20_EDS/', EDS)
        if node_id != 0 and EDS != '':
            nodes[node_id] = network.add_node(node_id, EDS_PATH)
            if DEBUG:
                print('Addind remote node: ', hex(node_id))
                print(nodes)
            reply_cmd = 'add_node'
            reply_parameters['node_id'] = node_id
        else:
            reply_cmd = 'err: node_id CANNOT be zero OR EDS cannot be empty'

    # ===========================================================
    # Scanner
    elif cmd == 'scanner':
        # Scan network with scanner via Index 0x1000 Subindex 0x00
        network.scanner.search()
        # Wait for nodes to respond
        time.sleep(1)
        if DEBUG:
            for node_id in network.scanner.nodes:
                print('Found node: ', hex(node_id))
        reply_cmd = 'scanner'
        reply_parameters = network.scanner.nodes

    # ===========================================================
    # SDO Upload
    elif cmd == 'sdo_upload':
        node_id = parameters.get('node_id', 0x00)
        index = parameters.get('index', 0x0000)
        subindex = parameters.get('subindex', 0x00)
        mode = parameters.get('mode', 'expedited')
        if node_id != 0x00 and index != 0x0000:
            if mode == 'expedited' or mode == 'segmented':
                obj = network[node_id].sdo[index]
                if isinstance(obj, canopen.sdo.Variable):
                    value =  obj.raw
                else:
                    value = obj[subindex].raw
            elif mode == 'block-filelike':
                # Upload large data (binary) via BLOCK transfer from the node via file-like access
                fp = network[node_id].sdo.open(index, subindex, 'rb', block_transfer=True) # rb = read binary
                value = fp.read()
                fp.close()
            else:
                pass
            reply_cmd = cmd
            reply_parameters['index'] = index
            reply_parameters['subindex'] = subindex
            reply_parameters['value'] = value
        else:
            reply_cmd = 'err: node_id CANNOT be zero OR index CANNOT be zero'

    # ===========================================================
    # SDO Download
    elif cmd == 'sdo_download':
        node_id = parameters.get('node_id', 0x00)
        index = parameters.get('index', 0x0000)
        subindex = parameters.get('subindex', 0x00)
        mode = parameters.get('mode', 'expedited')
        data = parameters.get('data', '')
        if node_id != 0x00 and index != 0x0000:
            if mode == 'expedited' or mode == 'segmented':
                obj = network[node_id].sdo[index]
                if isinstance(obj, canopen.sdo.Variable):
                    network[node_id].sdo[index].raw = data
                else:
                    network[node_id].sdo[index][subindex].raw = data
            else:
                # Download large data via BLOCK transfer from the node via file-like access
                fp = network[node_id].sdo.open(index, subindex, 'wb', block_transfer=True)
                fp.write(data)
                fp.close()
            reply_cmd = cmd
            reply_parameters['index'] = index
            reply_parameters['subindex'] = subindex
            reply_parameters['success'] = 0x01 # Permanently TRUE (= 0x01)
        else:
            reply_cmd = 'err: node_id CANNOT be zero OR index CANNOT be zero'

    # ===========================================================
    # Read active EMCYs
    elif cmd == 'emcys_read_active':
        node_id = parameters.get('node_id', 0x00)
        if node_id != 0x00:
            value = network[node_id].emcy.active
            value_str = str(network[node_id].emcy.active)
            reply_cmd = cmd
            reply_parameters['node_id'] = node_id
            reply_parameters['value'] = value_str
        else:
            reply_cmd = 'err: node_id CANNOT be zero'
    
    # ===========================================================
    # Read log EMCYs
    elif cmd == 'emcys_read_log':
        node_id = parameters.get('node_id', 0x00)
        if node_id != 0x00:
            value = network[node_id].emcy.log
            value_str = str(network[node_id].emcy.log)
            reply_cmd = cmd
            reply_parameters['node_id'] = node_id
            reply_parameters['value'] = value_str
        else:
            reply_cmd = 'err: node_id CANNOT be zero'

    # ===========================================================
    # Read next msg with specific CAN-ID
    elif cmd == 'subscribe_next_msg':
        can_id = parameters.get('can_id', 0x00000000)
        timeout = parameters.get('timeout', 3)
        subscribe_msg_count = 0
        subscribe_msg_id = 0
        subscribe_msg_data = []
        subscribe_msg_timestamp = 0
        time_waited = 0
        network.subscribe(can_id, _recv_callback)
        while subscribe_msg_count != 1 and time_waited <= timeout:
            time.sleep(0.1)
            time_waited = time_waited + 0.1
        network.unsubscribe(can_id, _recv_callback)
        reply_cmd = cmd
        if subscribe_msg_count == 1:
            reply_parameters['subscribe_msg_id'] = subscribe_msg_id
            reply_parameters['subscribe_msg_data'] = subscribe_msg_data
            reply_parameters['subscribe_msg_timestamp'] = subscribe_msg_timestamp
        else:
            reply_parameters['note'] = 'incorrect number of msgs received'

    # ===========================================================
    # Send raw CAN message
    elif cmd == 'can_send_msg':
        can_id = parameters.get('can_id', 0x00000000)
        can_bytes = parameters.get('can_bytes', [0xAB, 0xCD, 0xEF, 0x00, 0xAB, 0xCD, 0xEF, 0x99])
        network.send_message(can_id, can_bytes)
        reply_cmd = cmd
        reply_parameters['can_id'] = can_id
        reply_parameters['can_bytes'] = can_bytes

    # ===========================================================
    # Trigger EMCY
    elif cmd == 'emcys_trigger_sim':
        localSimNode_0x03.emcy.send(0x3001, register=4, data=b"Under")
        reply_cmd = cmd
        reply_parameters['node_id'] = node_id
        reply_parameters['value'] = 'triggered'

    # ===========================================================
    # Clear EMCY
    elif cmd == 'emcys_reset_sim':
        localSimNode_0x03.emcy.reset(register=4, data=b"CLEAR")
        reply_cmd = cmd
        reply_parameters['value'] = 'reset'

    # ===========================================================
    # Unknown CMD
    else:
        reply_cmd = 'unknown_cmd'

    result = {}
    result['reply_cmd'] = reply_cmd
    result['reply_parameters'] = reply_parameters

    if DEBUG:
        print(result)
    socket.send_string(json.dumps(result), encoding='utf-8')

# Disconnect networks from CAN bus
network.disconnect()

if SIM_NETWORK:
    network_sim.disconnect()
