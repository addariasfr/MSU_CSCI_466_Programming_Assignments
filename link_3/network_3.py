'''
Created on Oct 12, 2016

@author: mwittie
'''
import queue
import threading
from rprint import print


## wrapper class for a queue of packets
class Interface:
    ## @param max_queue_size - the maximum size of the queue storing packets
    #  @param mtu - the maximum transmission unit on this interface
    def __init__(self, max_queue_size=0):
        self.queue = queue.Queue(max_queue_size);
        self.mtu = 1

    ## get packet from the queue interface
    def get(self):
        try:
            return self.queue.get(False)
        except queue.Empty:
            return None

    ## put the packet into the interface queue
    # @param pkt - Packet to be inserted into the queue
    # @param block - if True, block until room in queue, if False may throw queue.Full exception
    def put(self, pkt, block=False):
        self.queue.put(pkt, block)


## Implements a network layer packet (different from the RDT packet 
# from programming assignment 2).
# NOTE: This class will need to be extended to for the packet to include
# the fields necessary for the completion of this assignment.
class NetworkPacket:
    ## packet encoding lengths
    dst_addr_S_length = 5
    f_flag_length = 1
    header_length = dst_addr_S_length + f_flag_length

    ##@param dst_addr: address of the destination host
    # @param data_S: packet payload
    # @param f_flag: fragmentation flag
    # @param offset: offset amount from the original packet
    def __init__(self, dst_addr, data_S, f_flag=0):
        self.dst_addr = dst_addr
        self.f_flag = f_flag
        self.data_S = data_S

    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()

    ## convert packet to a byte string for transmission over links
    def to_byte_S(self):
        byte_S = str(self.dst_addr).zfill(self.dst_addr_S_length)
        byte_S += str(self.f_flag).zfill(self.f_flag_length)
        byte_S += self.data_S
        return byte_S

    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        dst_addr = int(byte_S[0: self.dst_addr_S_length])
        f_flag = int(byte_S[self.dst_addr_S_length:self.header_length])
        data_S = byte_S[self.header_length:]
        return self(dst_addr, data_S, f_flag)


## Implements a network host for receiving and transmitting data
class Host:

    ##@param addr: address of this node represented as an integer
    def __init__(self, addr):
        self.addr = addr
        self.in_intf_L = [Interface()]
        self.out_intf_L = [Interface()]
        self.stop = False  # for thread termination
        self.received_data = ""

    ## called when printing the object
    def __str__(self):
        return 'Host_%s' % (self.addr)

    ## create a packet and enqueue for transmission
    # @param dst_addr: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    def udt_send(self, dst_addr, data_S, mtu):
        if len(data_S) > mtu - NetworkPacket.header_length:
            data_buffer = data_S
            f_index = 0
            while len(data_buffer) > 0:
                if len(data_buffer) > mtu:  # check if there is one packet left
                    p = NetworkPacket(dst_addr, data_buffer[:mtu - NetworkPacket.header_length],
                                      f_flag=1)  # create packet
                    print(
                        '%s: sending packet "%s" on the out interface with mtu=%d' % (self, p, self.out_intf_L[0].mtu))
                    self.out_intf_L[0].put(p.to_byte_S())  # send packets always enqueued successfully
                    data_buffer = data_buffer[
                                  mtu - NetworkPacket.header_length:]  # remove the sent data from the buffer
                else:  # if there only than one packet left
                    p = NetworkPacket(dst_addr, data_buffer[:mtu - NetworkPacket.header_length])  # create packet
                    print(
                        '%s: sending packet "%s" on the out interface with mtu=%d' % (self, p, self.out_intf_L[0].mtu))
                    self.out_intf_L[0].put(p.to_byte_S())  # send packets always enqueued successfully
                    data_buffer = data_buffer[
                                  mtu - NetworkPacket.header_length:]  # remove the sent data from the buffer
        else:
            p = NetworkPacket(dst_addr, data_S)
            print('%s: sending packet "%s" on the out interface with mtu=%d' % (self, p, self.out_intf_L[0].mtu))
            self.out_intf_L[0].put(p.to_byte_S())  # send packets always enqueued successfully

    ## receive packet from the network layer
    def udt_receive(self):
        pkt_S = self.in_intf_L[0].get()
        if pkt_S is not None:
            p = NetworkPacket.from_byte_S(pkt_S)
            print('%s: received packet "%s" on the in interface' % (self, pkt_S))
            self.received_data += p.data_S
            if p.f_flag == 0:
                print('Assembled fragmented packets into: ' + self.received_data)
                self.received_data = ""

    ## thread target for the host to keep receiving data
    def run(self):
        print(threading.currentThread().getName() + ': Starting')
        while True:
            # receive data arriving to the in interface
            self.udt_receive()
            # terminate
            if (self.stop):
                print(threading.currentThread().getName() + ': Ending')
                return


## Implements a multi-interface router described in class
class Router:

    ##@param name: friendly router name for debugging
    # @param intf_count: the number of input and output interfaces
    # @param max_queue_size: max queue length (passed to Interface)
    def __init__(self, name, intf_count, max_queue_size, rt):
        self.stop = False  # for thread termination
        self.name = name
        self.rt = rt
        # create a list of interfaces
        self.in_intf_L = [Interface(max_queue_size) for _ in range(intf_count)]
        self.out_intf_L = [Interface(max_queue_size) for _ in range(intf_count)]

    ## called when printing the object
    def __str__(self):
        return 'Router_%s' % (self.name)

    ## look through the content of incoming interfaces and forward to
    # appropriate outgoing interfaces
    def forward(self):
        for i in range(len(self.in_intf_L)):
            pkt_S = None
            try:
                # get packet from interface i
                pkt_S = self.in_intf_L[i].get()
                # if packet exists make a forwarding decision
                if pkt_S is not None:
                    p = NetworkPacket.from_byte_S(pkt_S)  # parse a packet out
                    # HERE you will need to implement a lookup into the
                    # forwarding table to find the appropriate outgoing interface
                    # for now we assume the outgoing interface is also i
                    if i in self.rt:  # if there is an entry in the table for the incoming interface number
                        print('%s: forwarding packet "%s" from interface %d to %d with mtu %d'
                              % (self, p, i, self.rt[i], self.out_intf_L[self.rt[i]].mtu))
                        self.out_intf_L[self.rt[i]].put(p.to_byte_S())  # forward the packet according to the table
                    else:  # if there isn't an entry in the table for the incoming interface number
                        print('%s: forwarding packet "%s" from interface %d to %d with mtu %d'
                              % (self, p, i, self.rt[p.dst_addr], self.out_intf_L[self.rt[p.dst_addr]].mtu))
                        self.out_intf_L[self.rt[p.dst_addr]].put(p.to_byte_S())  # forward the packet based on dest addr
            except queue.Full:
                print('%s: packet "%s" lost on interface %d' % (self, p, i))
                pass

    ## thread target for the host to keep forwarding data
    def run(self):
        print(threading.currentThread().getName() + ': Starting')
        while True:
            self.forward()
            if self.stop:
                print(threading.currentThread().getName() + ': Ending')
                return
