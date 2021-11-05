'''
Created on Oct 12, 2016

@author: mwittie
'''

import network_3
import link_3
import threading
from time import sleep
from rprint import print

## configuration parameters
router_queue_size = 0  # 0 means unlimited
simulation_time = 20  # give the network sufficient time to transfer all packets before quitting

if __name__ == '__main__':
	object_L = []  # keeps track of objects, so we can kill their threads

	# create network nodes
	client_1 = network_3.Host(1)
	object_L.append(client_1)
	client_2 = network_3.Host(2)
	object_L.append(client_1)
	server_1 = network_3.Host(3)
	object_L.append(server_1)
	server_2 = network_3.Host(4)
	router_a = network_3.Router(name='A', intf_count=2, max_queue_size=router_queue_size, rt={0: 0, 1: 1})
	router_b = network_3.Router(name='B', intf_count=1, max_queue_size=router_queue_size, rt={0: 0})
	router_c = network_3.Router(name='C', intf_count=1, max_queue_size=router_queue_size, rt={0: 0})
	# routing table based on destination addr for terminal router
	router_d = network_3.Router(name='D', intf_count=2, max_queue_size=router_queue_size, rt={2: 0, 3: 1})
	object_L.append(router_a)
	object_L.append(router_b)
	object_L.append(router_c)
	object_L.append(router_d)

	# create a Link Layer to keep track of links between network nodes
	link_layer = link_3.LinkLayer()
	object_L.append(link_layer)

	# add all the links
	# link parameters: from_node, from_intf_num, to_node, to_intf_num, mtu
	link_layer.add_link(link_3.Link(client_1, 0, router_a, 0, 30))  # Host1 - RouterA
	link_layer.add_link(link_3.Link(client_2, 0, router_a, 1, 30))  # Host2 - RouterA
	link_layer.add_link(link_3.Link(router_a, 0, router_b, 0, 30))  # RouterA - RouterB
	link_layer.add_link(link_3.Link(router_a, 1, router_c, 0, 30))  # RouterA - RouterC
	link_layer.add_link(link_3.Link(router_b, 0, router_d, 0, 30))  # RouterB - RouterD
	link_layer.add_link(link_3.Link(router_c, 0, router_d, 1, 30))  # RouterC - RouterD
	link_layer.add_link(link_3.Link(router_d, 0, server_1, 0, 30))  # RouterD - Host3
	link_layer.add_link(link_3.Link(router_d, 1, server_2, 0, 30))  # RouterD - Host4

	# start all the objects
	thread_L = [threading.Thread(name=object.__str__(), target=object.run) for object in object_L]
	for t in thread_L:
		t.start()

	# create some send events
	client_1.udt_send(2,
					  "From c 1 to s 1",
					  link_layer.link_L[0].in_intf.mtu)
	client_1.udt_send(3,
					  "From c 1 to s 2",
					  link_layer.link_L[0].in_intf.mtu)
	client_2.udt_send(2,
					  "From c 2 to s 1",
					  link_layer.link_L[0].in_intf.mtu)
	client_2.udt_send(3,
					  "From c 2 to s 2",
					  link_layer.link_L[0].in_intf.mtu)

	# give the network sufficient time to transfer all packets before quitting
	sleep(simulation_time)

	# join all threads
	for o in object_L:
		o.stop = True
	for t in thread_L:
		t.join()

	print("All simulation threads joined")
