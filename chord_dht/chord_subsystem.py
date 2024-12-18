import zmq
import hashlib
from typing import Optional, Self
from rich import print
from rich.text import Text
import threading
import time

# Operation codes
CHORD_SUBSYSTEM = b"Chord"

FIND_SUCCESSOR = b"Find_S"
FIND_PREDECESSOR = b"Find_P"
GET_SUCCESSOR = b"Get_S"
GET_PREDECESSOR = b"Get_P"
NOTIFY = b"Notify"
PING = b"Ping"
CLOSEST_PRECEDING_FINGER = b"Closest_PF"
# STORE_KEY = b"Store_K"
# RETRIEVE_KEY = b"Retrieve_K"


def getShaRepr(data: str):
    """Function to hash a string using SHA-1 and return its integer representation"""
    return int(hashlib.sha1(data.encode()).hexdigest(), 16)


def get_id_of_node(ip: str, port: int) -> int:
    """Returns the ID of the Chord Node associated with the IP:Port address"""
    return getShaRepr(f"{ip}:{port}")


class ChordNodeReference:
    def __init__(
        self,
        ip: str,
        port: int = 8001,
        context: Optional[zmq.SyncContext] = None,
    ):
        self.context: zmq.SyncContext = (
            context if context else zmq.SyncContext.instance()
        )
        """The zmq context to create sockets"""
        self.id = get_id_of_node(ip, port)
        """The unique ID of this `ChordNodeReference` in the Chord Ring"""
        self.ip: str = ip
        """The IP address of this `ChordNodeReference` in the Ring"""
        self.port: int = port
        """The Port of this `ChordNodeReference` in the Ring"""
        self.timeout: int = 2500
        """The timeout of each request in milliseconds"""

    def to_zmq_multipart(self) -> list[bytes]:
        """Creates a ZMQ multipart message that represents this node reference"""
        return [self.ip.encode(), self.port.to_bytes()]

    def send_data(self, data: list[bytes]) -> Optional[list[bytes]]:
        """Send data to this `ChordNodeReference and wait for a result.
        If no results are received after `self.timeout` then None is returned"""
        socket: zmq.SyncSocket = self.context.socket(zmq.DEALER)
        socket.setsockopt(zmq.LINGER, 0)
        response: Optional[list[bytes]] = None
        try:
            with socket.connect(f"tcp://{self.ip}:{self.port}") as conn:
                message = [CHORD_SUBSYSTEM] + data
                conn.send_multipart(message)
                items = conn.poll(self.timeout)
                if items != 0:  # If we receive something
                    response = conn.recv_multipart()
        except Exception as e:
            print(
                f"An exception occurred in the `send_data` method of `ChordNodeReference` => \n{e}"
            )
        socket.close(0)
        return response

    def find_successor(self, id: int) -> Optional[Self]:
        """Finds the `ChordNodeReference` of the immediate successor of the `id`"""
        response = self.send_data([FIND_SUCCESSOR, id.to_bytes()])
        if not response:
            return None
        ip = response[0].decode()
        port = int.from_bytes(response[1])
        return ChordNodeReference(ip, port, self.context)

    def find_predecessor(self, id: int) -> Optional[Self]:
        """Finds the `ChordNodeReference` of the immediate predecessor of the `id`"""
        response = self.send_data([FIND_PREDECESSOR, id.to_bytes()])
        if not response:
            return None
        ip = response[0].decode()
        port = int.from_bytes(response[1])
        return ChordNodeReference(ip, port, self.context)

    @property
    def successor(self) -> Optional[Self]:
        """Returns the successor of this node"""
        response = self.send_data([GET_SUCCESSOR, id.to_bytes()])
        if not response:
            return None
        ip = response[0].decode()
        port = int.from_bytes(response[1])
        return ChordNodeReference(ip, port, self.context)

    @property
    def predecessor(self) -> Optional[Self]:
        """Returns the predecessor of this node"""
        response = self.send_data([GET_PREDECESSOR, id.to_bytes()])
        if not response:
            return None
        ip = response[0].decode()
        port = int.from_bytes(response[1])
        return ChordNodeReference(ip, port, self.context)

    def closest_preceding_finger(self, id: int) -> Optional[Self]:
        """Find the closest preceding finger preceding the `id`"""
        response = self.send_data([CLOSEST_PRECEDING_FINGER, id.to_bytes()])
        if not response:
            return None
        ip = response[0].decode()
        port = int.from_bytes(response[1])
        return ChordNodeReference(ip, port, self.context)

    def notify(self, node: Self):
        """This function notify this node about another node that is potentially it's predecessor"""
        self.send_data([NOTIFY] + node.to_zmq_multipart())

    def ping(self) -> bool:
        """This function makes a ping to the node. It return True if the node is alive"""
        response = self.send_data([PING])
        return response is not None


class ChordNode:
    """This class implements the logic of a Chord Node.
    But it works as a subsystem of another bigger system. That's why
    this class doesn't create a socket for listening. The class receives
    a socket given from the bigger system and from that socket is from where we listen
    for messages"""

    def __init__(
        self,
        context: zmq.SyncContext,
        server_socket: zmq.SyncSocket,
        ip: str,
        port: int = 8001,
        m: int = 160,
    ):
        self.server_socket: zmq.SyncSocket = server_socket
        """The socket from where this `ChordNode` will receive messages"""
        self.context: zmq.SyncContext = context
        """The zmq context for creating new sockets"""
        self.id: int = get_id_of_node(ip, port)
        """The unique ID of this node in the Chord Ring"""
        self.ip = ip
        """The IP address of this `ChordNode`"""
        self.port = port
        """The port of this `ChordNode`"""
        self.ref: ChordNodeReference = ChordNodeReference(self.ip, self.port)
        """The Chord reference to this node. Use this to make calls to yourself"""
        self.successor: ChordNodeReference = self.ref  # Initial successor is itself
        """The successor `ChordNodeReference` of this node"""
        self.predecessor: Optional[ChordNodeReference] = (
            None  # Initially no predecessor
        )
        """The predecessor `ChordNodeReference` of this node"""
        self.m: int = m
        """Number of bits in the hash/key space"""
        self.finger = [self.ref] * self.m  # Finger table
        """Finger Table of this `ChordNode`. It includes the actual node as the first reference"""

        threading.Thread(target=self.stabilize, daemon=True).start()
        threading.Thread(target=self.fix_fingers, daemon=True).start()
        threading.Thread(target=self.start_server, daemon=True).start()
        threading.Thread(target=self.check_predecessor, daemon=True).start()

    def find_successor(self, id: int) -> ChordNodeReference:
        """Finds the `ChordNodeReference` of the immediate successor of the `id`"""
        # TODO: Verify this
        node = self.find_predecessor(id)
        return node.successor

    def _in_between(self, k: int, start: int, end: int) -> bool:
        """Helper method to check if a value is between (start, end]"""
        return start < k <= end

    def find_predecessor(self, id: int) -> ChordNodeReference:
        """Finds the `ChordNodeReference` of the immediate predecessor of the `id`"""
        # TODO: Verify this
        node = self
        while not node.id < id <= node.successor.id:
            new_node = node.closest_preceding_finger(id)
            if node.id == new_node.id:
                break
            node = new_node
        node = ChordNodeReference(
            node.ip, node.port
        )  # This conversion is in the case of returning `self` which is a `ChordNode`
        return node

    def notify(self, node: ChordNodeReference):
        """This function notify this node about another node that is potentially it's predecessor"""
        if not self.predecessor or self._in_between(
            node.id, self.predecessor.id, self.id
        ):
            self.predecessor = node

    def closest_preceding_finger(self, id: int) -> ChordNodeReference:
        """Find the closest preceding finger preceding the `id`"""
        for i in range(self.m - 1, -1, -1):
            if self.finger[i] and self._in_between(self.finger[i].id, self.id, id):
                return self.finger[i]

    def join(self, node: ChordNodeReference):
        """Join this `ChordNode` to the ring of the given node"""
        if node.id == self.id:
            return
        self.predecessor = None
        self.successor = node.find_successor(self.id)

    def stabilize(self):
        """Keep the successor up to date"""
        while True:
            try:
                pred = self.successor.predecessor
                if self.id < pred.id <= self.successor.id:
                    self.predecessor = pred
            except Exception as e:
                print(f"An exception occurred in 'Stabilize' method => \n{e}")
            time.sleep(1)

    def fix_fingers(self):
        """Fix the finger table periodically"""
        while True:
            try:
                for i in range(self.m - 1, -1, -1):
                    start = (self.id + 2**i) % (2**self.m)
                    self.finger[i] = self.find_successor(start)
                    time.sleep(0.05)
            except Exception as e:
                print(
                    f"An error occur in the `fix_fingers` method of the node => \n{e}"
                )
            time.sleep(10)

    def check_predecessor(self):
        """Check for the predecessor"""
        while True:
            try:
                self.predecessor = (
                    self.predecessor
                    if self.predecessor and self.predecessor.ping()
                    else None
                )
            except Exception as e:
                print(
                    f"An exception has occurred in the `check_predecessor` routine => \n{e}"
                )
            time.sleep(1)

    def stop(self):
        """This method stop the subsystem. Closing all sockets and stopping all threads"""
        # Implement this
        pass

    def start_server(self):
        # TODO: The response format should handle the address of the node that made the request
        while True:
            try:
                message = self.server_socket.recv_multipart()
                """The first part of all messages must be 'Chord'"""
                assert (
                    len(message) >= 3
                ), "Chord subsystem expects at least 3 parts in a message (id, subsystem, operation)"

                client_address, subsystem, operation, *body = message
                assert (
                    subsystem == CHORD_SUBSYSTEM
                ), f"The first part of the message MUST be `{CHORD_SUBSYSTEM.decode()}` but it was received `{subsystem.decode()}`"

                response: Optional[list[bytes]] = (
                    None  # The response to the actual request
                )

                if operation == FIND_SUCCESSOR:
                    id = int.from_bytes(body[0])
                    successor = self.find_successor(id)
                    response = successor.to_zmq_multipart()
                elif operation == FIND_PREDECESSOR:
                    id = int.from_bytes(body[0])
                    predecessor = self.find_predecessor(id)
                    response = predecessor.to_zmq_multipart()
                elif operation == GET_SUCCESSOR:
                    # TODO: Verify this implementation
                    successor = self.successor if self.successor else self.ref
                    response = successor.to_zmq_multipart()
                elif operation == GET_PREDECESSOR:
                    # TODO: Verify this implementation
                    predecessor = self.predecessor if self.predecessor else self.ref
                    response = predecessor.to_zmq_multipart()
                elif operation == NOTIFY:
                    assert (
                        len(body) == 2
                    ), f"The NOTIFY operation requires 2 arguments. The IP address and Port"
                    ip = body[0]
                    port = int.from_bytes(body[1])
                    node = ChordNodeReference(ip, port)
                    self.notify(node)
                elif operation == PING:
                    response = [b""]
                elif operation == CLOSEST_PRECEDING_FINGER:
                    id = int.from_bytes(body[0])
                    node = self.closest_preceding_finger(id)
                    response = node.to_zmq_multipart()
                else:
                    raise Exception(f"Operation not supported => '{operation}'")

                if response:
                    # Handle how to send the response to the upper layer system
                    self.server_socket.send_multipart([client_address] + response)

            except Exception as e:
                print(
                    Text(
                        f"An error has occurred in the 'start_server' of Chord =>\n{str(e)}",
                        style="red",
                    )
                )
