from network_3 import Router, Host
from link_3 import Link, LinkLayer
import threading
from time import sleep
from rprint import print

##configuration parameters
router_queue_size = 0 #0 means unlimited
simulation_time = 20 #give the network sufficient time to execute transfers

if __name__ == '__main__':
    object_L = [] #keeps track of objects, so we can kill their threads at the end
    
    #create network hosts
    host_1 = Host('H1')
    object_L.append(host_1)
    host_2 = Host('H2')
    object_L.append(host_2)
    host_3 = Host('H3')
    object_L.append(host_3)
    
    #create routers and routing tables for connected clients (subnets)
    encap_tbl_D = {'H1': 'RB', 'H2': 'RC'}  # Router A is the only ingress router for the MPLS domain and thus has an encapsulation table
    frwd_tbl_D = {'H1': ('', 0), 'H2': ('', 1), 'RB': ('RD', 2), 'RC': ('RD', 3)}  # table used to forward AND decapsulate MPLS frames
    router_a = Router(name='RA', 
                              intf_capacity_L=[500,500,500,500],
                              encap_tbl_D = encap_tbl_D,
                              frwd_tbl_D = frwd_tbl_D,
                              max_queue_size=router_queue_size)
    object_L.append(router_a)

    encap_tbl_D = {}  # interior routers in the MPLS domain do not need an encapsulation table as they only forward MPLS packets
    frwd_tbl_D = {'RD': ('H2', 1)}  # Router B knows forward packets labeled for RD with the new label H2
    router_b = Router(name='RB', 
                              intf_capacity_L=[500,100],  # the interface connected to RD has a bottleneck
                              encap_tbl_D = encap_tbl_D,
                              frwd_tbl_D = frwd_tbl_D,
                              max_queue_size=router_queue_size)
    object_L.append(router_b)

    encap_tbl_D = {}  # interior routers in the MPLS domain do not need an encapsulation table as they only forward MPLS packets
    frwd_tbl_D = {'RD': ('H2', 1)}  # Router C knows forward packets labeled for RD with the new label H2
    router_c = Router(name='RC', 
                              intf_capacity_L=[500,500],
                              encap_tbl_D = encap_tbl_D,
                              frwd_tbl_D = frwd_tbl_D,
                              max_queue_size=router_queue_size)
    object_L.append(router_c)

    encap_tbl_D = {}  # Router D is solely used as an egress router to the MPLS domain and thus does not need an encapsulation table
    frwd_tbl_D = {'H2': ('', 2)}  # Router D knows to decapsulate packets and send them out interface 2
    router_d = Router(name='RD', 
                              intf_capacity_L=[500,100,500],  # the interface connected to RC has a bottleneck
                              encap_tbl_D = encap_tbl_D,
                              frwd_tbl_D = frwd_tbl_D,
                              max_queue_size=router_queue_size)
    object_L.append(router_d)
    
    #create a Link Layer to keep track of links between network nodes
    link_layer = LinkLayer()
    object_L.append(link_layer)
    
    #add all the links - need to reflect the connectivity in cost_D tables above
    link_layer.add_link(Link(host_1, 0, router_a, 0))
    link_layer.add_link(Link(host_2, 0, router_a, 1))
    link_layer.add_link(Link(router_a, 2, router_b, 0))
    link_layer.add_link(Link(router_a, 3, router_c, 0))
    link_layer.add_link(Link(router_b, 1, router_d, 0))
    link_layer.add_link(Link(router_c, 1, router_d, 1))
    link_layer.add_link(Link(router_d, 2, host_3, 0))
    
    
    #start all the objects
    thread_L = []
    for obj in object_L:
        thread_L.append(threading.Thread(name=obj.__str__(), target=obj.run)) 
    
    for t in thread_L:
        t.start()
    
    #create some send events    
    for i in range(5):
        priority = i%2
        host_1.udt_send('H3', 'H1', 'MESSAGE_%d_FROM_H1' % i, priority)
        host_2.udt_send('H3', 'H2', 'MESSAGE_%d_FROM_H2' % i, priority)
        
    #give the network sufficient time to transfer all packets before quitting
    sleep(simulation_time)

    
    #join all threads
    for o in object_L:
        o.stop = True
    for t in thread_L:
        t.join()
        
    print("All simulation threads joined")