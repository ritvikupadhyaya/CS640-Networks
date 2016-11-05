#!/usr/bin/env python3

'''
Ethernet learning switch in Python: HW3.

Note that this file currently has the code to implement a "hub"
in it, not a learning switch.  (I.e., it's currently a switch
that doesn't learn.)
'''
from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.common import *
import threading
import time

forwardList = {}
time_thread = threading.Timer(None, None)

def switchy_main(net):
    my_interfaces = net.interfaces() 
    # TODO: construct a dict with <ethaddr : port> pair
    global forwardList, time_thread, exit
    forwardList = dict([(intf.ethaddr.toStr(), [intf.name, currnt_time_in_sec()+30]) for intf in my_interfaces]) 
    # call timeout functiion
    timeout()
    while True:
        try:
            # dev -> device name
            # packet -> packet receive
            dev,packet = net.recv_packet()
        except NoPackets:
            continue
        except Shutdown:
            return

        # drop packet if dst addr is indentical to the interface MAC
        dropPacket = False
        for intf in my_interfaces:
            if packet[0].dst.toStr() == intf.ethaddr.toStr():
                dropPacket = True
        if dropPacket:
            print ("Packet to interface MAC dropped.")
            continue
        log_debug ("In {} received packet {} on {}".format(net.name, packet, dev))
        # TODO: if the source MAC addr. not seen before, add it to the forward table.
        srcAddr = packet[0].src.toStr()
        if srcAddr not in forwardList:
            forwardList[srcAddr] = [dev, currnt_time_in_sec()+30]
        if packet[0].dst.toStr() in forwardList:
            # update dev(interface) if device moved.
            time = forwardList[srcAddr][1]
            if not forwardList[srcAddr][0] == dev:
                forwardList[srcAddr] = [dev, time]
            # packet[0] - header for the packet
            # other data in the header: dst, src, ethertype
            log_debug ("Packet intended for me")
            # TODO: look up port for dst addr. and forward the packet to that port.
            net.send_packet(forwardList[packet[0].dst.toStr()][0], packet)
        else:
            for intf in my_interfaces:
                if dev != intf.name:
                    log_debug ("Flooding packet {} to {}".format(packet, intf.name))
                    net.send_packet(intf.name, packet)
    net.shutdown()

def timeout():
    global time_thread, forwardList
    # clean stale entries
    update_List = {}
    for key, value in forwardList.items():
        if (value[1] > currnt_time_in_sec()):
            update_List[key] = value
    forwardList = update_List
    # update timer thread for timeout
    if (threading.main_thread().is_alive()):
        # if main fucntion still alive
        time_thread = threading.Timer(2.0, timeout)
        time_thread.start()
    else: 
        time_thread.cancel()

# code soure for get current time, please refer to README.md
def currnt_time_in_sec():
    current_time = lambda: int(round(time.time() * 1000))
    return int(current_time()/1000)