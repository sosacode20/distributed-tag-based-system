from pydantic import BaseModel, Field, model_validator, UUID4
from service_announcement import ServiceAnnouncement
import time
from datetime import datetime, timezone
from typing import *
import uuid
from loguru import logger


class Peer(BaseModel):
    """This class is used to store the information of a peer"""

    uuid: UUID4 = Field(description="The UUID of the peer", default=uuid.uuid4())
    """The UUID of the peer"""

    service: ServiceAnnouncement = Field(
        description="The service information of the peer"
    )
    """The service configuration"""
    expiration_time: datetime = Field(
        description="The UTC time when the peer expires",
        default_factory=lambda: datetime.now(timezone.utc),
        exclude=True,
    )
    """The UTC time when the peer expires"""

    def __eq__(self, value):
        if isinstance(value, Peer):
            return self.uuid == value.uuid
        return False

    def is_expired(self) -> bool:
        """Check if the peer has expired"""
        # Get the current time and compare it with the expiration time in UTC
        return datetime.now(timezone.utc) > self.expiration_time

    def update_expiration_time(self, expiration_time: datetime) -> None:
        """Update the expiration time of the peer"""
        self.expiration_time = expiration_time.astimezone(timezone.utc)

    def to_json(self):
        """Convert the object to a JSON string"""
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str):
        """Create an instance of the class from a JSON string"""
        res = uuid.uuid4().hex.encode("utf-8")
        return cls.model_validate_json(json_str)

    # @model_validator(mode="after")
    # def pos_init(self) -> Self:
    #     self.expiration_time = self.expiration_time.astimezone(timezone.utc)
    #     return self


class PeerRegistry(BaseModel):
    """This class is used to store the peers"""

    services_and_peers: dict[str, list[Peer]] = Field(
        description="The dictionary of peers per service",
        default={},
    )
    """The dictionary of services and the peers that offered it"""
    max_peers_per_service: int = Field(
        gt=0,
        lt=50,
        description="The maximum number of peers per service",
        default=10,
    )
    """The maximum number of peers per service"""

    # @model_validator(mode="after")
    # def pos_init(self) -> Self:
    #     self.logger = logger.bind(where="PeerRegistry")
    #     """The logger for the class"""
    #     return self

    def add_peer(self, peer: Peer) -> None:
        """Add a peer to the registry"""
        with logger.contextualize(inside="add_peer", peer=peer):
            logger.info("Adding a peer...")
            res = self.services_and_peers.get(peer.service.service, [])
            res.append(peer)
            self.services_and_peers[peer.service.service] = res
            if len(res) > self.max_peers_per_service:
                peers = res
                logger.bind(peers=peers).info("List before adding the peer")
                peers.pop(0)
                logger.bind(peers=peers).info("List after adding the peer")

    def remove_peer(self, peer: Peer) -> None:
        """Remove a peer from the registry"""
        with logger.contextualize(inside="remove_peer", peer=peer):
            logger.info("Removing a peer")
            try:
                peers = self.services_and_peers[peer.service.service]
                logger.bind(peers=peers).info("List before removing the peer")
                peers.remove(peer)
                logger.bind(peers=peers).info("List after removing the peer")
            except Exception as e:
                logger.error(f"Error trying to remove a peer that doesn't exist: {e}")
                raise e

    def get_peers(self, service_name: str, max_amount: int) -> list[Peer]:
        """Get a list of the most recent joined peers from the registry"""
        with logger.contextualize(
            inside="get_peer",
            service_name=service_name,
            max_amount=max_amount,
        ):
            result = self.services_and_peers.get(service_name, [])
            result = result[-max_amount:]
            logger.info("Returning list of peers")
            return result

    def get_all_peers(self) -> list[Peer]:
        """Get all peers from the registry"""
        with logger.contextualize(inside="get_all_peers"):
            result = []
            for peers in self.services_and_peers.values():
                result.extend(peers)

            logger.info("Getting all the peers in the register")
            return result
