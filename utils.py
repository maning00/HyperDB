from absl import logging
import hashlib
from iroha import IrohaCrypto
from simhash import Simhash
import jieba


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
    def __init__(self, id, name, timestamp, author, email, institution, environment, parameters, details, attachment, hash=None, offset=-1):
        self.id = id
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
        self.offset = offset
        self.simhash = None

    def cal_hash(self):
        """
        Return hash of data.
        """
        data = '{}{}{}{}{}{}{}{}{}'.format(self.name, self.timestamp, self.author, self.email, self.institution, self.environment, self.parameters, self.details, self.attachment)

        return hashlib.sha256(data.encode('utf-8'))

    def cal_simhash(self):
        data = '{};{};{};{};{};{};{};{};{}'.format(self.name, self.timestamp, self.author, self.email, self.institution, self.environment, self.parameters, self.details, self.attachment)
        words = jieba.lcut(data)
        return Simhash(words)

    @classmethod
    def from_tuple(cls, tuple):
        """
        Create an entry from query results.
        """
        return cls(tuple[0], tuple[1], tuple[2], tuple[3], tuple[4], tuple[5], tuple[6], tuple[7], tuple[8], tuple[9], tuple[10], tuple[11])
