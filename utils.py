from absl import logging
import hashlib
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


class Entry:
    """
    Store the database entry in a class
    """
    def __init__(self, name, timestamp, author, email, institution, environment, parameters, details, attachment, hash=None):
        self.name = name
        self.timestamp = timestamp
        self.author = author
        self.email = email
        self.institution = institution
        self.environment = environment
        self.parameters = parameters
        self.details = details
        self.attachment = attachment
        self.hash = hash

    def cal_hash(self):
        """
        Return hash of data.
        """
        data = '{}{}{}{}{}{}{}{}'.format(self.name, self.timestamp, self.author, self.email, self.institution, self.environment, self.parameters, self.details, self.attachment)
        return hashlib.sha256(data.encode('utf-8'))
