from dataclasses import dataclass, field

from wiregen.classes.interface import Interface
from wiregen.classes.peer import Peer

@dataclass
class ConfigFile:
    """"""
    interface: Interface
    peers: list[Peer] = field(default_factory=list)

    def __post_init__(self):
        if isinstance(self.peers, Peer):
            self.peers = [self.peers]

    def __str__(self) -> str:
        """ 
        Render the config file as s string
        """
        return '\n'.join([str(self.interface) + '\n'] + [str(i) + '\n' for i in self.peers])