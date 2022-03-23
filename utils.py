from absl import logging
import binascii
from iroha import IrohaCrypto


def trace(func):
    """
    A decorator for tracing methods' begin/end execution points
    """

    def tracer(*args, **kwargs):
        name = func.__name__
        print('\tEntering "{}"'.format(name))
        result = func(*args, **kwargs)
        print('\tLeaving "{}"'.format(name))
        return result

    return tracer


class Keypair:
    """
    Store the private key and public key in a class.
    """

    def __init__(self, private_key, public_key):
        self.private_key = private_key
        self.public_key = public_key

    def __str__(self):
        return '{} {}'.format(self.private_key, self.public_key)
