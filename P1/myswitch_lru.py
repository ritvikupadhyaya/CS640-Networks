#!usr/bin/env python3

from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.common import *

def switchy_main(net):
    my_interfaces = net.interfaces()
    mymacs = [intf.ethaddr for intf in my_interfaces]
    lruList = []
    while True:
        try:
            dev,packet = net.recv_packet()
        except NoPackets:
            continue
        except Shutdown:
            return
        #Check to see if the source is in the table
        sources = [lruItems[0] for lruItems in lruList]
        if not packet[0].src in sources:
           #If we have less than 5 elements then just add the new entry as the first one
           if len(lruList) < 5:
                lruList.insert(0,[packet[0].src, dev])
           else:
                #Remove the last entry and then add the new source entry in the table
                lruList.pop()
                lruList.insert(0,[packet[0].src, dev])
        else:
             #Check to see if the port matches as we learned in the past.
             if not [packet[0].src, dev] in lruList:
                    for index, items in enumerate(lruList):
                        if items[0] == packet[0].src and items[1] != dev:
                            lruList.pop(index)
                            lruList.insert(index, [packet[0].src, dev])
                            break

        log_debug ("In {} received packet {} on {}".format(net.name, packet, dev))
        destsources = [lruItems[0] for lruItems in lruList]
        if packet[0].dst in mymacs:
            log_debug ("Packet intended for me")
        else:
            #update the MRU entry for the destination address
            if packet[0].dst in destsources:
              indexOfDest = destsources.index(packet[0].dst)
              itemToRem = lruList[indexOfDest]
              lruList.remove(itemToRem)
              lruList.insert(0,itemToRem)
              net.send_packet(itemToRem[1], packet)
            else:
              for intf in my_interfaces:
                if dev != intf.name:
                    log_debug ("Flooding packet {} to {}".format(packet, intf.name))
                    net.send_packet(intf.name, packet)
    net.shutdown()
