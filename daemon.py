from iroha import Iroha, IrohaGrpc
from utils import *



class Daemon:
    """
    chaindb daemon.
    """
    def __init__(self, addr, port, domain_name):
        self.net = IrohaGrpc('{}:{}'.format(addr, port))
        self.domain = domain_name

