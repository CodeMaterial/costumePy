import time
import logging
import zmq
import threading
import CostumePy
from collections import deque


class CospyManager:

    def __init__(self):
        self._node_sockets = {}
        self._listeners = {}
        self.running = True
        self._manager_listeners = {"_listen_for": self.register_listener}
        self.backlog = deque()

        self.context = zmq.Context()

        self.request_socket = self.context.socket(zmq.REP)
        self.request_socket.bind("tcp://*:55556")

        self.available_ip = 55557

        self.ip_address_manager = threading.Thread(target=self.manage_ip_requests)
        self.ip_address_manager.start()

    def stop(self):
        self.running = False
        self.ip_address_manager.join()

    def manage_ip_requests(self):

        while self.running:
            try:
                node_name = self.request_socket.recv_string(flags=zmq.NOBLOCK)

                if node_name in self._node_sockets:
                    logging.error("Node already running %s" % node_name)
                    self.request_socket.send_string("FAILED")
                    continue

                address = "tcp://localhost:%i" % self.available_ip
                self.request_socket.send_string(address)
                soc = self.context.socket(zmq.PAIR)
                for i in range(10):
                    try:
                        soc.bind("tcp://*:%i" % self.available_ip)
                        break
                    except zmq.error.ZMQError:  # TODO make this recursive, or semi recursive
                        logging.error("Can't assign socket number %s, iterating" % self.available_ip)
                        self.available_ip += 1
                self._node_sockets[node_name] = soc
                self.available_ip += 1
            except:
                pass

    def register_listener(self, msg):
        topic, node_name = msg["data"], msg["source"]
        logging.info("Registering  %s for %s" % (node_name, topic))

        if topic not in self._listeners:
            self._listeners[topic] = []

        if node_name not in self._listeners[topic]:
            self._listeners[topic].append(node_name)

        msg = CostumePy.message("_success", data=msg)

        self._node_sockets[node_name].send_json(msg)

    def delete_socket(self, node_name):
        self._node_sockets[node_name].close()
        del self._node_sockets[node_name]

    def action(self, msg):

        if msg["action_at"] <= time.time():

            logging.info("Received message %r" % msg)

            topic = msg["topic"]

            if topic == "death":
                self.delete_socket(msg["source"])

            if topic in self._manager_listeners:
                self._manager_listeners[topic](msg)
            else:
                if topic in self._listeners:
                    for nodes_listening in self._listeners[topic]:
                        if nodes_listening in self._node_sockets:
                            logging.info("Sending %r to %s" % (msg, nodes_listening))
                            self._node_sockets[nodes_listening].send_json(msg, zmq.NOBLOCK)
                else:
                    logging.info("No one listening to %s" % msg)

        else:
            self.backlog.appendleft(msg)

    def run(self):

        logging.info("Starting queue management")

        try:
            while self.running:
                for node_name in list(self._node_sockets):
                    try:
                        soc = self._node_sockets[node_name]
                        msg = soc.recv_json(flags=zmq.NOBLOCK)
                        msg["source"] = node_name
                        self.action(msg)

                    except zmq.Again:
                        pass

                    if self.backlog:
                        self.action(self.backlog.pop())

        finally:
            self.stop()
