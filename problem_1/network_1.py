import queue
import threading
import json
import copy
from rprint import print


# wrapper class for a queue of packets
class Interface:
    # @param maxsize - the maximum size of the queue storing packets
    def __init__(self, maxsize=0):
        self.in_queue = queue.Queue(maxsize)
        self.out_queue = queue.Queue(maxsize)
    
    # get packet from the queue interface
    # @param in_or_out - use 'in' or 'out' interface
    def get(self, in_or_out):
        try:
            if in_or_out == 'in':
                pkt_S = self.in_queue.get(False)
                # if pkt_S is not None:
                #     print('getting packet from the IN queue')
                return pkt_S
            else:
                pkt_S = self.out_queue.get(False)
                # if pkt_S is not None:
                #     print('getting packet from the OUT queue')
                return pkt_S
        except queue.Empty:
            return None
    
    # put the packet into the interface queue
    # @param pkt - Packet to be inserted into the queue
    # @param in_or_out - use 'in' or 'out' interface
    # @param block - if True, block until room in queue, if False may throw queue.Full exception
    def put(self, pkt, in_or_out, block=False):
        if in_or_out == 'out':
            # print('putting packet in the OUT queue')
            self.out_queue.put(pkt, block)
        else:
            # print('putting packet in the IN queue')
            self.in_queue.put(pkt, block)


# Implements a network layer packet.
class NetworkPacket:
    # packet encoding lengths
    dst_S_length = 5
    src_S_length = 5
    prot_S_length = 1
    
    # @param dst: address of the destination host
    # @param data_S: packet payload
    # @param prot_S: upper layer protocol for the packet (data, or control)
    # @param src (default: None): address of the sending router
    def __init__(self, dst, prot_S, data_S, src=0):
        self.dst = dst
        self.src = src
        self.data_S = data_S
        self.prot_S = prot_S
    
    # called when printing the object
    def __str__(self):
        return self.to_byte_S()
    
    # convert packet to a byte string for transmission over links
    def to_byte_S(self):
        byte_S = str(self.dst).zfill(self.dst_S_length)
        byte_S += str(self.src).zfill(self.src_S_length)
        if self.prot_S == 'data':
            byte_S += '1'
        elif self.prot_S == 'control':
            byte_S += '2'
        else:
            raise ('%s: unknown prot_S option: %s' % (self, self.prot_S))
        byte_S += self.data_S
        return byte_S
    
    # extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        dst = byte_S[0: NetworkPacket.dst_S_length].strip('0') if byte_S[0: NetworkPacket.dst_S_length] != '00000' else 0
        src = byte_S[NetworkPacket.dst_S_length: NetworkPacket.dst_S_length + NetworkPacket.src_S_length].strip('0') if byte_S[NetworkPacket.dst_S_length: NetworkPacket.dst_S_length + NetworkPacket.src_S_length] != '00000' else 0
        prot_S = byte_S[NetworkPacket.dst_S_length + NetworkPacket.src_S_length: NetworkPacket.dst_S_length + NetworkPacket.src_S_length + NetworkPacket.prot_S_length]
        if prot_S == '1':
            prot_S = 'data'
        elif prot_S == '2':
            prot_S = 'control'
        else:
            raise ('%s: unknown prot_S field: %s' % (self, prot_S))
        data_S = byte_S[NetworkPacket.dst_S_length + NetworkPacket.src_S_length + NetworkPacket.prot_S_length:]
        return self(dst, prot_S, data_S, src)


# Implements a network host for receiving and transmitting data
class Host:
    
    # @param addr: address of this node represented as an integer
    def __init__(self, addr):
        self.addr = addr
        self.intf_L = [Interface()]
        self.stop = False  # for thread termination
    
    # called when printing the object
    def __str__(self):
        return self.addr
    
    # create a packet and enqueue for transmission
    # @param dst: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    def udt_send(self, dst, data_S):
        p = NetworkPacket(dst, 'data', data_S)
        print('%s: sending packet "%s"' % (self, p))
        self.intf_L[0].put(p.to_byte_S(), 'out')  # send packets always enqueued successfully
    
    # receive packet from the network layer
    def udt_receive(self):
        pkt_S = self.intf_L[0].get('in')
        if pkt_S is not None:
            print('%s: received packet "%s"' % (self, pkt_S))
    
    # thread target for the host to keep receiving data
    def run(self):
        print(threading.currentThread().getName() + ': Starting')
        while True:
            # receive data arriving to the in interface
            self.udt_receive()
            # terminate
            if (self.stop):
                print(threading.currentThread().getName() + ': Ending')
                return


# Implements a multi-interface router
class Router:
    
    # @param name: friendly router name for debugging
    # @param cost_D: cost table to neighbors {neighbor: {interface: cost}}
    # @param max_queue_size: max queue length (passed to Interface)
    def __init__(self, name, cost_D, max_queue_size):
        self.stop = False  # for thread termination
        self.name = name
        # create a list of interfaces
        self.intf_L = [Interface(max_queue_size) for _ in range(len(cost_D))]
        # save neighbors and interfeces on which we connect to them
        self.cost_D = cost_D  # {neighbor: {interface: cost}}
        # TODO: set up the routing table for connected hosts
        self.rt_tbl_D = {}  # {destination: {router: cost}}
        for dst in cost_D:  # add each neighbor cost to the routing table
            self.rt_tbl_D[dst] = cost_D[dst]
        print('%s: Initialized routing table' % self)
        self.print_routes()
    
    # Print routing table
    def print_routes(self):
        print("Routing table at %s" % self.name)
        # TODO: print the routes as a two dimensional table
        print(self.rt_tbl_D)
        #print('___________________________')
        #print('| ' + self.name + ' | H1 | H2 | RA | RB |')
        #print('___________________________')
        #print('| RA |  ' + str(self.rt_tbl_D['H1'][0]) + ' |  ' + str(self.rt_tbl_D['H2'][1]) + ' |  0 |  ' + str(self.rt_tbl_D['RB'][1]) + ' |')
        #print('___________________________')
        #print('| RB |  ' + str(self.rt_tbl_D['H1'][0]) + ' |  ' + str(self.rt_tbl_D['H2'][1]) + ' |  ' + str(self.rt_tbl_D['RB'][1]) + ' |  0 |')
        #print('___________________________')
    
    # called when printing the object
    def __str__(self):
        return self.name
    
    # look through the content of incoming interfaces and
    # process data and control packets
    def process_queues(self):
        for i in range(len(self.intf_L)):
            pkt_S = None
            # get packet from interface i
            pkt_S = self.intf_L[i].get('in')
            # if packet exists make a forwarding decision
            if pkt_S is not None:
                p = NetworkPacket.from_byte_S(pkt_S)  # parse a packet out
                if p.prot_S == 'data':
                    self.forward_packet(p, i)
                elif p.prot_S == 'control':
                    self.update_routes(p, i)
                else:
                    raise Exception('%s: Unknown packet type in packet %s' % (self, p))
    
    # forward the packet according to the routing table
    #  @param p Packet to forward
    #  @param i Incoming interface number for packet p
    def forward_packet(self, p, i):
        try:
            min_cost = 99999  # initialize cost arbitrarily high
            out_i = -1  # initialize outgoing interface
            for dst in self.rt_tbl_D:
                if dst == p.dst:  # if table entry matches the packet destination
                    for rt in self.rt_tbl_D[dst]:  # for each outgoing router
                        if self.rt_tbl_D[dst][rt] < min_cost:  # if cost to router is the lowest
                            out_i = rt  # set outgoing interface
                            min_cost = self.rt_tbl_D[dst][rt]  # set the min cost
            self.intf_L[out_i].put(p.to_byte_S(), 'out', True)  # put the packet on the out interface
            print('%s: forwarding packet "%s" from interface %d to %d' % (self, p, i, 1))
        except queue.Full:
            print('%s: packet "%s" lost on interface %d' % (self, p, i))
            pass
    
    # send out route update
    # @param i Interface number on which to send out a routing update
    def send_routes(self, i):
        # TODO: Send out a routing table update
        # create a routing table update packet
        table_s = json.dumps(self.rt_tbl_D)
        p = NetworkPacket(i, 'control', table_s, self.name)
        try:
            print('%s: sending routing update "%s" from interface %d' % (self, p, i))
            self.intf_L[i].put(p.to_byte_S(), 'out', True)
        except queue.Full:
            print('%s: packet "%s" lost on interface %d' % (self, p, i))
            pass
    
    # forward the packet according to the routing table
    #  @param p Packet containing routing information
    def update_routes(self, p, i):
        # TODO: add logic to update the routing tables and
        #  possibly send out routing updates
        print('%s: Received routing update %s from interface %d' % (self, p, i))
        prev_table = copy.deepcopy(self.rt_tbl_D)
        table_s = json.loads(p.data_S)
        p_dst = int(p.dst)  # get the packet destination integer
        for dst in table_s:  # for each dst in the packet table
            if dst not in self.rt_tbl_D:  # if dst isnt int this table
                #if dst != self.name:  # if dst is not this router

                    # cast sub keys to ints
                    temp_table = copy.deepcopy(table_s)  # copy the table for iteration
                    for dest in temp_table:  # for each dst in copy table
                        for rtr in temp_table[dest]:  # for each rtr in dst's routes
                            table_s[dest][int(rtr)] = table_s[dest].pop(rtr)  # set the key to an int

                    self.rt_tbl_D[dst] = table_s[dst]  # set the route to dst in this table
                    for rtr in self.rt_tbl_D[dst]:  # for each router to dst in this table
                        self.rt_tbl_D[dst][int(rtr)] += table_s[self.name][p_dst]  # add the cost from the sender to this router
            else:  # if dst is in this table

                # cast sub keys to ints
                temp_table = copy.deepcopy(table_s)
                for dest in temp_table:
                    for rtr in temp_table[dest]:
                        table_s[dest][int(rtr)] = table_s[dest].pop(rtr)

                for rtr in table_s[dst]:  # for each router in dst's routes
                    if rtr not in self.rt_tbl_D[dst]:  # if the cost to dst thru rtr doesn't exist in this table
                        self.rt_tbl_D[dst][rtr] = table_s[dst][rtr] + table_s[self.name][p_dst]  # add cost thru rtr + cost to this router to this table
                    else:  # this table has a cost thru rtr to dst
                        if table_s[dst][rtr] < self.rt_tbl_D[dst][rtr]:  # if the packet table's cost is less than this table's cost
                            self.rt_tbl_D[dst][int(rtr)].update(table_s[dst][rtr] + table_s[self.name][p_dst])  # replace the 
        if prev_table != self.rt_tbl_D:
            [self.send_routes(out_i) for out_i in range(len(self.intf_L))]
        #if prev_table != self.rt_tbl_D:
        #    self.send_routes(i)
        #for dst in self.rt_tbl_D:
        #    for router in self.rt_tbl_D[dst]:
        #        router = int(router)
        #print('%s: Received routing update %s from interface %d' % (self, p, i))
    
    # thread target for the host to keep forwarding data
    def run(self):
        print(threading.currentThread().getName() + ': Starting')
        while True:
            self.process_queues()
            if self.stop:
                print(threading.currentThread().getName() + ': Ending')
                return
