from absl import logging
import binascii
from iroha import IrohaCrypto


def trace(func):
    """
    A decorator for tracing methods' begin/end execution points
    """

    def tracer(*args, **kwargs):
        name = func.__name__
        logging.info('Entering %s', name)
        result = func(*args, **kwargs)
        logging.info('Leaving %s', name)
        return result

    return tracer


@trace
def send_transaction_and_print_status(net, transaction):
    """
    Sends a transaction to the Iroha network and prints its status.
    """

    hex_hash = binascii.hexlify(IrohaCrypto.hash(transaction))
    logging.info('Transaction hash = %s, creator = %s',
        hex_hash, 
        transaction.payload.reduced_payload.creator_account_id)
    net.send_tx(transaction)
    for status in net.tx_status_stream(transaction):
        logging.info(status)


class Keypair:
    """
    Store the private key and public key in a class.
    """
    def __init__(self, private_key, public_key):
        self.private_key = private_key
        self.public_key = public_key
    
    def __str__(self):
        return '{} {}'.format(self.private_key, self.public_key)