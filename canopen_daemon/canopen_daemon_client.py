#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    canopen-daemon-client

    An exemplary client to connect to the canopen-daemon via ZMQ

    use-case:
    NI TestStand  <--->  LabVIEW  <--->  ZMQ  <--->  canopen-daemon  <--->  CANopen network
    
    Author: Niels Göran Blume
    Company: embeX GmbH, Freiburg im Breisgau, Germany
"""

import time
import logging
import os
import struct
import json

import zmq

DEBUG = False

context = zmq.Context()

def build_msg(cmd, parameters):
    message = {}
    message['cmd'] = cmd
    message['parameters'] = parameters

    return message

def send_cmd(cmd, parameters):
    print('--------')
    # Send CMD
    message = build_msg(cmd, parameters)
    print('Request: ', json.dumps(message))
    socket.send_string(json.dumps(message), encoding='utf-8', )

    # Receive cmd Response
    # ToDo: Utilize TIMEOUT
    reply = socket.recv_string(encoding='utf-8')
    print('Reply: %s' % (reply))
    reply_dict = json.loads(reply)

    return reply_dict

#  Socket to talk to server
print('Connecting to canopen_daemon at tcp://localhost:5555 …')
socket = context.socket(zmq.REQ)
socket.connect('tcp://localhost:5555')

reply_dict = send_cmd('add_node', {'node_id': 0x03, 'EDS': 'SimNode/SimNode.eds'})

reply_dict = send_cmd('nmt_change_state', {'node_id': 0x03, 'new_state': 'INITIALISING'})
time.sleep(1)

reply_dict = send_cmd('sdo_download', {'node_id': 0x03, 'index': 0x1017, 'subindex': 0x00, 'mode': 'expedited', 'data': 2500})

reply_dict = send_cmd('nmt_change_state', {'node_id': 0x03, 'new_state': 'PRE-OPERATIONAL'})
time.sleep(1)

reply_dict = send_cmd('pdo_start_tx', {'node_id': 0x03, 'pdo_number':1, 'period': 2.5})
time.sleep(1)

reply_dict = send_cmd('pdo_start_tx', {'node_id': 0x03, 'pdo_number':2, 'period': 4.5})
time.sleep(1)

reply_dict = send_cmd('nmt_change_state', {'node_id': 0x03, 'new_state': 'OPERATIONAL'})
time.sleep(1)

reply_dict = send_cmd('scanner', {})

reply_dict = send_cmd('sync_activate_periodic', {'sync_period': 1.5})

reply_dict = send_cmd('sdo_upload', {'node_id': 0x03, 'index': 0x1000, 'subindex': 0x00, 'mode': 'expedited'})

reply_dict = send_cmd('sdo_upload', {'node_id': 0x03, 'index': 0x1008, 'subindex': 0x00, 'mode': 'segmented'})

reply_dict = send_cmd('sdo_upload', {'node_id': 0x03, 'index': 0x1018, 'subindex': 0x04, 'mode': 'expedited'})

# Object is RO to arhere to CiA profile standards
# reply_dict = send_cmd('sdo_download', {'node_id': 0x03, 'index': 0x1008, 'subindex': 0x00, 'mode': 'segmented', 'data': 'embeX Node - ID 0x03'})

reply_dict = send_cmd('sdo_upload', {'node_id': 0x03, 'index': 0x1008, 'subindex': 0x00, 'mode': 'segmented'})

reply_dict = send_cmd('sdo_download', {'node_id': 0x03, 'index': 0x6001, 'subindex': 0x01, 'mode': 'expedited', 'data': 0x01})

time.sleep(5)

reply_dict = send_cmd('sdo_download', {'node_id': 0x03, 'index': 0x6001, 'subindex': 0x01, 'mode': 'expedited', 'data': 0x1F})

time.sleep(5)

reply_dict = send_cmd('sdo_download', {'node_id': 0x03, 'index': 0x6011, 'subindex': 0x01, 'mode': 'expedited', 'data': 0xFFFFFFFF})

time.sleep(5)

reply_dict = send_cmd('sdo_download', {'node_id': 0x03, 'index': 0x6011, 'subindex': 0x02, 'mode': 'expedited', 'data': 0xBBFFAAFF})

reply_dict = send_cmd('sync_deactivate_periodic', {})
time.sleep(10)

reply_dict = send_cmd('emcys_read_active', {'node_id': 0x03})

reply_dict = send_cmd('emcys_read_log', {'node_id': 0x03})

reply_dict = send_cmd('emcys_trigger_sim', {})
time.sleep(1)

reply_dict = send_cmd('emcys_read_active', {'node_id': 0x03})

reply_dict = send_cmd('emcys_read_log', {'node_id': 0x03})

reply_dict = send_cmd('emcys_reset_sim', {})
time.sleep(1)

reply_dict = send_cmd('emcys_read_active', {'node_id': 0x03})

reply_dict = send_cmd('emcys_read_log', {'node_id': 0x03})

reply_dict = send_cmd('subscribe_next_msg', {'can_id': 0x1AF, 'timeout': 15})

reply_dict = send_cmd('can_send_msg', {'can_id': 0x00F, 'can_bytes': [0x00, 0x00, 0xFF, 0xFF, 0x00, 0x00, 0xFF, 0xFF]})

reply_dict = send_cmd('turn_off', {})
