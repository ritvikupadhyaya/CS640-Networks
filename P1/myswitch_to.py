#!usr/bin/env python3

from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.common import *
import time

def switchy_main(net):
    my_interfaces = net.interfaces()
    mymacs = [intf.ethaddr for intf in my_interfaces]
    toList = {}
    
    while True:
        try:
            dev,packet = net.recv_packet()
        except NoPackets:
            continue
        except Shutdown:
            return

        #Update the time out entries in the table.
        newToList = {}
        for key, value in toList.items():
            if (value[1] > int(int(round(time.time() * 1000))/1000)):
               newToList[key] = value
        toList = newToList

        #If there is not entry for the source, add the entry with the time out time.
        if not packet[0].src in toList:
           toList[packet[0].src] = [dev, int(int(round(time.time() * 1000))/1000)+10]
        else:
            #Check the packet has the same port as earlier and update the port and reset timeout
             if not toList[packet[0].src][0] == dev:
                   toList[packet[0].src][0] = dev
             toList[packet[0].src][1] = int(int(round(time.time() * 1000))/1000)+10


        log_debug ("In {} received packet {} on {}".format(net.name, packet, dev))
        if packet[0].dst in mymacs:
            log_debug ("Packet intended for me")

        else:
            if packet[0].dst in toList:
              net.send_packet(toList[packet[0].dst][0], packet)
            else:
              for intf in my_interfaces:
                if dev != intf.name:
                    log_debug ("Flooding packet {} to {}".format(packet, intf.name))
                    net.send_packet(intf.name, packet)
    net.shutdown()
