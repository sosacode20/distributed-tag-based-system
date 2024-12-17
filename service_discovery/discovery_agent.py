import zmq
from udp_multicast import MulticastHelper, MulticastGroup
import uuid
import asyncio
from service_announcement import ServiceAnnouncement
import datetime as dt
from dns_registry import Peer
from loguru import logger
from scheduler import Scheduler
from pydantic import ValidationError

JOINED = b"JOINED"
"""The message to send when a peer joins the network"""
LEFT = b"LEFT"
"""The message to send when a peer leaves the network"""
KILL = b"KILL"
"""The message to send to kill the service watcher updater"""


class DiscoveryAgent(object):
    ctx: zmq.Context
    """The zmq context"""
    pipe: zmq.Socket
    """The pipe to communicate with the service watcher"""
    udp: MulticastHelper
    """The multicast helper"""
    peers: dict[uuid.UUID, Peer] = {}
    """The list of peers living in the network"""
    loop: asyncio.AbstractEventLoop
    """The asyncio loop"""
    ping_task: asyncio.Task
    """The task to send pings"""

    def __init__(
        self,
        parent_ctx: zmq.Context,
        pipe: zmq.Socket,
        expiration_time: dt.timedelta = dt.timedelta(seconds=3),
        announcements: list[ServiceAnnouncement] = [],
        # enable_logs: bool = True,
    ):
        self.ctx = parent_ctx
        self.pipe = pipe
        group = MulticastGroup()

        # self.loop = self._get_loop()

        # self.udp = MulticastHelper(group=group, loop=self.loop)
        self.udp = MulticastHelper(group=group)
        """The multicast helper"""
        self.expiration_time: dt.timedelta = expiration_time
        """The expiration time for each peer registered"""
        self.my_peer_announcements: list[Peer] = self.create_peers_from_announcements(
            announcements
        )
        """The list of peer announcements to send as pings"""
        self.logger = logger.bind(where="DiscoveryAgent")
        """The logger for this class"""
        self.logger.info("Created the discovery agent")
        # self.logger.info("Calling async-io run method")
        # asyncio.run(self.run())
        # self.run()

    def create_peers_from_announcements(
        self, announcements: list[ServiceAnnouncement] = []
    ):
        """Create a list of peers for the announcements"""
        my_peer_announces = [Peer(service=a) for a in announcements]
        return my_peer_announces

    def stop(self):
        """Stop the discovery agent"""
        self.logger.bind(inside="stop").info("Stopping the discovery agent")
        self.pipe.close()
        if self.loop:
            self.loop.stop()

    def __del__(self):
        try:
            self.stop()
        except Exception as e:
            self.logger.bind(exception=e).exception(f"An error occurred")
            raise e

    def _get_loop(self):
        """Get the asyncio event loop"""
        # try:
        #     loop = asyncio.get_running_loop()
        # except:
        loop = asyncio.get_event_loop()
        return loop

    def start(self):
        asyncio.run(self.run())

    async def run(self):
        """Run the discovery agent"""
        self.logger.info("Entering the run method of the discovery agent")

        loop = self.loop = asyncio.get_running_loop()
        self.udp.set_loop(loop=loop)
        schedule = Scheduler(loop=loop)

        # schedule.cyclic(dt.timedelta(seconds=3), self.check_for_peer_pings)
        self.logger.info("Creating the task 'check_pings' in async-io loop")
        # ping = loop.create_task(self.check_for_peer_pings())
        self.ping_task = asyncio.create_task(self.check_for_peer_pings())
        # loop.add_reader(self.udp.socket.fileno(), self.check_pings)
        # loop.tas

        self.logger.info("Registering 'send_ping_info' in scheduler class")
        schedule.cyclic(dt.timedelta(seconds=3), self.send_ping_info)
        self.logger.info("Registering 'remove_dead_peers' in scheduler class")
        schedule.cyclic(dt.timedelta(seconds=1), self.remove_dead_peers)

        # loop.run_forever()
        # asyncio.gather(self.check_for_peer_pings())
        while True:
            await asyncio.sleep(3600)
        # await self.ping_task

    async def check_pings(self):
        log = self.logger.bind(inside="check_pings")
        log.info("Waiting for a message")
        message = await self.udp.receive()
        self.logger.info(f"Received message: {message}")
        try:
            log.info("Parsing with Pydantic the message..")
            peer = Peer.from_json(message.decode("utf-8"))
            log.info(f"peer ping received: {peer}")
            new_expiration_time: dt.datetime = (
                dt.datetime.now(tz=dt.timezone.utc) + self.expiration_time
            )
            if peer.uuid in self.peers:
                log.info(f"Peer {peer} already in the list")
                self.peers[peer.uuid].update_expiration_time(new_expiration_time)
                log.info(f"Updated Expiration Time of Peer to: {new_expiration_time}")
            else:
                log.info(f"Peer {peer} not in the list")
                peer.update_expiration_time(new_expiration_time)
                self.peers[peer.uuid] = peer
                log.info(f"Peer {peer} added to the list of peers")
                self.pipe.send_multipart([JOINED, peer.to_json().encode("utf-8")])
            # peer =
        except ValidationError as e:
            self.logger.error(f"Error parsing message: {e}")

    async def check_for_peer_pings(self):
        """Checks for announcements in the network"""
        log = self.logger.bind(inside="check_for_peer_pings")
        while True:
            log.info("Waiting for message")
            message = await self.udp.receive()
            # self.logger.info(f"Received message: {message}")
            try:
                log.info("Parsing with Pydantic the message..")
                peer = Peer.from_json(message.decode("utf-8"))
                log.info(f"peer ping received: {peer}")
                new_expiration_time: dt.datetime = (
                    dt.datetime.now(tz=dt.timezone.utc) + self.expiration_time
                )
                if peer.uuid in self.peers:
                    log.info(f"Peer {peer} already in the list")
                    self.peers[peer.uuid].update_expiration_time(new_expiration_time)
                    log.info(
                        f"Updated Expiration Time of Peer to: {new_expiration_time}"
                    )
                else:
                    log.info(f"Peer {peer} not in the list")
                    peer.update_expiration_time(new_expiration_time)
                    self.peers[peer.uuid] = peer
                    log.info(f"Peer {peer} added to the list of peers")
                    self.pipe.send_multipart([JOINED, peer.to_json().encode("utf-8")])
                # peer =
            except ValidationError as e:
                self.logger.error(f"Error parsing message: {e}")
            except Exception as e:
                self.logger.error(f"An unknown error has occurred -> {e}")

    async def send_ping_info(self):
        """Send the ping information to the network"""
        with self.logger.contextualize(inside="send_ping_info"):
            for peer in self.my_peer_announcements:
                self.logger.info(f"Sending announcement: {peer}")
                await self.udp.send(peer.to_json().encode("utf-8"))

    async def remove_dead_peers(self):
        with self.logger.contextualize(inside="remove_dead_peers"):
            self.logger.info("Removing dead peers")
            peers = [peer for peer in self.peers.values()]
            for peer in peers:
                if peer.is_expired():
                    self.logger.info(f"Peer {peer} is expired")
                    del self.peers[peer.uuid]
                    self.pipe.send_multipart([LEFT, peer.to_json().encode("utf-8")])
                else:
                    self.logger.info(f"Peer {peer} is still alive")
