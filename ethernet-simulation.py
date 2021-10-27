import simpy
import random
import math
import numpy as np
import matplotlib.pyplot as plt
import sys


# First  define some global variables. You should change values
class G:
    RANDOM_SEED = 33
    SIM_TIME = 50000   # This should be large
    SLOT_TIME = 1
    N = int(sys.argv[1]) # The first command-line argument is the number of nodes to simulate
    ARRIVAL_RATE = float(sys.argv[3]) # The third command-line argument is the arrival rate lambda
    RETRANMISSION_POLICIY = sys.argv[2] # The second command-line argument is the retransmission polic: ”pp”, ”op”, ”beb”, or ”lb”
    LONG_SLEEP_TIMER = 1000000000

        
class Server_Process(object):
    def __init__(self, env, dictionary_of_nodes, retran_policy, slot_stat):
        self.env = env
        self.dictionary_of_nodes = dictionary_of_nodes 
        self.retran_policy = retran_policy 
        self.slot_stat = slot_stat
        self.current_slot = 0
        self.action = env.process(self.run())
            
    def run(self):
        # print("Server process started")
        
        while True: 
            # sleep for slot time
            yield self.env.timeout(G.SLOT_TIME)
            
            # Code to determine what happens to a slot and 
            # then update node variables accordingly based 
            # on the algorithm
            self.current_slot += 1
            self.slot_stat.addTotal()
            
            # p-persistent policies for both p values
            if self.retran_policy == "pp" or self.retran_policy == "op":
                node_number = [] # list of the nodes trying to transmit this slot
                
                # different retransmission p value depnding on different policies
                retran_p = 0.5
                if self.retran_policy == "op":
                    retran_p = 1 / G.N
                    
                # find active nodes
                for i in list(range(1,G.N+1)):
                    # first time transmit packet
                    if self.dictionary_of_nodes[i].hasPacket == True and self.dictionary_of_nodes[i].isRetran == False:
                        node_number.append(i)
                    elif self.dictionary_of_nodes[i].hasPacket == True and self.dictionary_of_nodes[i].isRetran == True:
                        # nodes which has packet retransmit with possibility retran_p
                        if random.uniform(0,1) < retran_p:
                            node_number.append(i)
                            
                # determine if slot is success
                if len(node_number) == 1:
                    # successful slot: only one node transmitting
                    self.dictionary_of_nodes[node_number[0]].queue.pop()
                    self.dictionary_of_nodes[node_number[0]].len -= 1
                    self.dictionary_of_nodes[node_number[0]].isRetran = False
                    if self.dictionary_of_nodes[node_number[0]].len == 0:
                        self.dictionary_of_nodes[node_number[0]].hasPacket = False
                    # add one to successfule slot
                    self.slot_stat.addSuccess()
                elif len(node_number) > 1:
                    # wasted slot: more than one node is transmitting
                    for i in node_number:
                        # find active nodes and marked them as retrans
                        self.dictionary_of_nodes[i].isRetran = True
                
            # binary expo backoff policy and linear backoff policy
            elif self.retran_policy == "beb" or self.retran_policy == "lb":
                node_number = [] # list of nodes to transmit packets
                # find active nodes
                for i in list(range(1,G.N+1)):
                    if self.dictionary_of_nodes[i].hasPacket == True:
                        # check if this node has packet to send and is scheduled to tranmit in this slot
                        if self.dictionary_of_nodes[i].retran_slot == 0:
                            node_number.append(i)
                        # otherwise, decrease the countdown for the nodes which has packet but not scheduled to retransmit this slot
                        elif self.dictionary_of_nodes[i].retran_slot > 0:
                            self.dictionary_of_nodes[i].retran_slot -= 1
                        
                            
                # determine if slot is success
                if len(node_number) == 1:
                    # successful slot: only one node transmitting
                    packet = self.dictionary_of_nodes[node_number[0]].queue.pop()
                    self.dictionary_of_nodes[node_number[0]].len -= 1
                    self.dictionary_of_nodes[node_number[0]].retran_attempt = 0
                    self.dictionary_of_nodes[node_number[0]].retran_slot = 0
                    if self.dictionary_of_nodes[node_number[0]].len == 0:
                        self.dictionary_of_nodes[node_number[0]].hasPacket = False
                    # add one to the successful slot
                    self.slot_stat.addSuccess()
                elif len(node_number) > 1:
                    # wasted slot: more than one node is transmitting
                    for i in node_number:
                        # find active nodes and set up retransmission slot according to different policies
                        if self.retran_policy == "beb":
                            # binary expo backoff
                            k_min = min(self.dictionary_of_nodes[i].retran_attempt, 10)
                            backoff = random.randint(0, 2**k_min)
                            self.dictionary_of_nodes[i].retran_slot = backoff
                            # update the attempt to retransmit
                            self.dictionary_of_nodes[i].retran_attempt += 1
                        elif self.retran_policy == "lb":
                            # linear backoff
                            k_min = min(self.dictionary_of_nodes[i].retran_attempt, 1024)
                            backoff = random.randint(0, k_min)
                            self.dictionary_of_nodes[i].retran_slot = backoff
                            # update the attempt to retransmit
                            self.dictionary_of_nodes[i].retran_attempt += 1
  
                    
        
class Node_Process(object): 
    def __init__(self, env, id, arrival_rate):
        
        self.env = env
        self.id = id
        self.arrival_rate = arrival_rate
        
        # Other state variables
        self.packet_number = 0
        self.len = 0 # length of packet buffer
        self.queue = [] # packet buffer
        self.isRetran = False # if this node is retransmitting packets
        self.hasPacket = False # if this node has packet to send in the buffer
        self.retran_slot = 0 # the number of slot delayed from the cuurent slot to retrans mit the packet 
        self.retran_attempt = 0 # number of attempts to retransmit the current packet
        
        self.action = env.process(self.run())
        

    def run(self):
        # packet arrivals 
        # print("Arrival Process Started:", self.id)
        
        # Code to generate the next packet and deal with it
        while True:
            yield self.env.timeout(random.expovariate(self.arrival_rate))
            # create and enque the new packet into the buffer
            self.packet_number += 1
            arrival_time = self.env.now  
            new_packet = Packet(self.packet_number,arrival_time)
            self.queue.append(new_packet)
            self.len += 1
            self.hasPacket = True

        
        
        

class Packet:
    def __init__(self, identifier, arrival_time):
        self.identifier = identifier
        self.arrival_time = arrival_time


class StatObject(object):    
    def __init__(self):
        self.dataset =[]
        self.success = 0 # number of successful slots
        self.total = 0 #number of total slots
        
    def addNumber(self,x):
        self.dataset.append(x)
        
    def addTotal(self):
        self.total += 1

    def addSuccess(self):
        self.success += 1
        
    def getThroughput(self):
        # throughput is defined as the number of successful transmission per time unit
        #  which in this case, can be found by number of successful slots / number of total slots
        return self.success / self.total




def main():
    print("Simiulation Analysis of Random Access Protocols")
    random.seed(G.RANDOM_SEED)

    env = simpy.Environment()
    slot_stat = StatObject()
    dictionary_of_nodes  = {} # I chose to pass the list of nodes as a 
                                      # dictionary since I really like python dictionaries :)
            
    for i in list(range(1,G.N+1)):
        node = Node_Process(env, i, G.ARRIVAL_RATE)
        dictionary_of_nodes[i] = node
    server_process = Server_Process(env, dictionary_of_nodes,G.RETRANMISSION_POLICIY,slot_stat)
    env.run(until=G.SIM_TIME)
            
    # code to print the result
    print("Number of Nodes:", G.N, end = ", ")
    print("Retransmission Policy:", G.RETRANMISSION_POLICIY, end = ", ")
    print("Arrival rate:", G.ARRIVAL_RATE, end = ", ")
    print("Throughput: %.2f"%round(slot_stat.getThroughput(), 2))
        
    
if __name__ == '__main__': main()
