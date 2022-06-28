from operator import le
import random
import math
import collections

class Node:
    def __init__(self, location, A, maxSimulationTime):
        self.queue = collections.deque(self.generate_queue(A, maxSimulationTime))
        self.location = location  # Defined as a multiple of D
        self.collisions = 0
        self.successfull_transmited_pakets = 0
        self.time = 0
        self.wt_success_packets = 0
        self.wt_collision = False
        self.wt_collisions_count = 0
        self.wait_collisions = 0
        self.MAX_COLLISIONS = 10
        self.windows_times = []

    def verify_window_time(self, curr_time):
        window_time = WindowTime(self.time, self.wt_success_packets, self.wt_collision, self.wt_collisions_count)
        self.windows_times.append(window_time)
        self.time = math.trunc(curr_time)
        self.wt_success_packets = 0
        self.wt_collision = False
        self.wt_collisions_count = 0

    def collision_occured(self, R):
        self.collisions += 1
        self.wt_collisions_count += 1
        self.wt_collision = True
        if self.collisions > self.MAX_COLLISIONS:
            # Drop packet and reset collisions
            return self.pop_packet()

        # Add the exponential backoff time to waiting time
        backoff_time = self.queue[0] + self.exponential_backoff_time(R, self.collisions)

        for i in range(len(self.queue)):
            if backoff_time >= self.queue[i]:
                self.queue[i] = backoff_time
            else:
                break

    def successful_transmission(self):
        self.queue.popleft()
        self.collisions = 0
        self.successfull_transmited_pakets += 1
        self.wt_success_packets += 1
        self.wait_collisions = 0

    def generate_queue(self, A, maxSimulationTime):
        packets = []
        arrival_time_sum = 0

        while arrival_time_sum <= maxSimulationTime:
            arrival_time_sum += self.get_exponential_random_variable(A)
            packets.append(arrival_time_sum)
        return sorted(packets)

    def exponential_backoff_time(self, R, general_collisions):
        rand_num = random.random() * (pow(2, general_collisions) - 1)
        return rand_num * 512/float(R)  # 512 bit-times

    def non_persistent_bus_busy(self, R):
        self.wait_collisions += 1
        if self.wait_collisions > self.MAX_COLLISIONS:
            # Drop packet and reset collisions
            return self.pop_packet()

        # Add the exponential backoff time to waiting time
        backoff_time = self.queue[0] + self.exponential_backoff_time(R, self.wait_collisions)

        for i in range(len(self.queue)):
            if backoff_time >= self.queue[i]:
                self.queue[i] = backoff_time
            else:
                break

    def get_exponential_random_variable(self, param):
        # Get random value between 0 (exclusive) and 1 (inclusive)
        uniform_random_value = 1 - random.uniform(0, 1)
        exponential_random_value = (-math.log(1 - uniform_random_value) / float(param))
        return exponential_random_value    

    def print_windows_times(self):
        for wt in self.windows_times:
            wt.print_data()

    def get_last_window_time(self, window_time):
        for i in range(len(self.windows_times)):
            if int(self.windows_times[i].time) == int(window_time):
                return self.windows_times[i]



class WindowTime():
    def __init__(self, time, success_packets, collision, collisions_count):
        self.time = time
        self.success_packets = success_packets
        self.collision = collision
        self.collisions_count = collisions_count


class CSMACD():

    def __init__(self):
        self.actual_window_time = 0
        self.curr_time = 0
        self.window_time_collisions = 0
        self.wt_successfully_transmitted_packets = 0
        self.collisions = 0
        self.transmitted_packets = 0
        self.successfully_transmitted_packets = 0
        self.nodes = []

    def restart_simulation(self):
        self.actual_window_time = 0
        self.curr_time = 0
        self.window_time_collisions = 0
        self.wt_successfully_transmitted_packets = 0
        self.collisions = 0
        self.transmitted_packets = 0
        self.successfully_transmitted_packets = 0
        self.nodes = []

    def get_window_time_host(self, window_time):
        data = ""
        for i in range(len(self.nodes)):
            data += "Host " + str(i) + " : " + str(self.nodes[i].get_last_window_time(window_time).success_packets) + "\n"
        return data

    def get_window_time_success_packets(self, window_time):
        success_packets = 0
        for node in self.nodes:
            success_packets += node.get_last_window_time(window_time).success_packets
        return success_packets
    
    def get_window_time_collisions(self, window_time):
        collisions_count = 0
        for node in self.nodes:
            collisions_count += node.get_last_window_time(window_time).collisions_count
        return collisions_count

    def build_nodes(self, N, A, D, maxSimulationTime):
        nodes = []
        for i in range(0, N):
            nodes.append(Node(i*D, A, maxSimulationTime))
        return nodes

    def csma_cd(self, N, A, R, L, D, S, maxSimulationTime, is_persistent):
        self.nodes = self.build_nodes(N, A, D, maxSimulationTime)
        while True:
            if math.trunc(self.curr_time) - self.actual_window_time == 1:
                self.actual_window_time = math.trunc(self.curr_time)
                for node in self.nodes:
                    node.verify_window_time(self.curr_time)
            # Step 1: Pick the smallest time out of all the nodes
            min_node = Node(None, A, maxSimulationTime)  # Some random temporary node
            min_node.queue = [float("infinity")]
            for node in self.nodes:
                if len(node.queue) > 0:
                    min_node = min_node if min_node.queue[0] < node.queue[0] else node

            if min_node.location is None:  # Terminate if no more packets to be delivered
                break

            self.curr_time = min_node.queue[0]
            self.transmitted_packets += 1

            # Step 2: Check if collision will happen
            # Check if all other nodes except the min node will collide
            collsion_occurred_once = False
            for node in self.nodes:
                if node.location != min_node.location and len(node.queue) > 0:
                    delta_location = abs(min_node.location - node.location)
                    t_prop = delta_location / float(S)
                    t_trans = L/float(R)

                    # Check collision
                    will_collide = True if node.queue[0] <= (self.curr_time + t_prop) else False

                    # Sense bus busy
                    if (self.curr_time + t_prop) < node.queue[0] < (self.curr_time + t_prop + t_trans):
                        if is_persistent is True:
                            for i in range(len(node.queue)):
                                if (self.curr_time + t_prop) < node.queue[i] < (self.curr_time + t_prop + t_trans):
                                    node.queue[i] = (self.curr_time + t_prop + t_trans)
                                else:
                                    break
                        else:
                            node.non_persistent_bus_busy(R)

                    if will_collide:
                        collsion_occurred_once = True
                        self.transmitted_packets += 1
                        node.collision_occured(R)

            # Step 3: If a collision occured then retry
            # otherwise update all nodes latest packet arrival times and proceed to the next packet
            #print("collision: ", collsion_occurred_once)
            if collsion_occurred_once is not True:  # If no collision happened
                self.successfully_transmitted_packets += 1
                self.wt_successfully_transmitted_packets += 1
                min_node.successful_transmission()
            else:    # If a collision occurred
                self.collisions += 1
                self.window_time_collisions += 1
                min_node.collision_occured(R)