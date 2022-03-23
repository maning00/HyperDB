#!/usr/bin/env python3

import os
import sys
from absl import app, flags

from daemon import *



FLAGS = flags.FLAGS
flags.DEFINE_string("iroha_addr", "127.0.0.1", "iroha host address.")
flags.DEFINE_integer("iroha_port", 50051, "iroha host port.")


@trace
def create_user(iroha, net, domain, user_name, admin_pk) -> Keypair:
    """
    Creates a user.
    """
    user_private_key = IrohaCrypto.private_key()
    user_public_key = IrohaCrypto.derive_public_key(user_private_key)

    tx = iroha.transaction([
        iroha.command('CreateAccount', account_name=user_name, domain_id=domain,
                      public_key=user_public_key)
    ])
    IrohaCrypto.sign_transaction(tx, admin_pk)
    send_transaction_and_print_status(net, tx)
    return Keypair(user_private_key, user_public_key)

        

@trace
def init_admin(domain_name='test', coin_name='icoin'):
    """
    Initializes the admin.
    """

    ADMIN_ACCOUNT_ID = os.getenv('ADMIN_ACCOUNT_ID', 'admin@test')
    ADMIN_PRIVATE_KEY = os.getenv(
    'ADMIN_PRIVATE_KEY', 'f101537e319568c765b2cc89698325604991dca57b9716b58016b253506cab70')
    iroha = Iroha(ADMIN_ACCOUNT_ID)
    net = IrohaGrpc('{}:{}'.format(FLAGS.iroha_addr, FLAGS.iroha_port))

    # tx = IrohaCrypto.sign_transaction(
    #     iroha.transaction([iroha.command('CreateDomain', domain_id=domain_name)]), ADMIN_PRIVATE_KEY)
    # send_transaction_and_print_status(net, tx)

    # tx = IrohaCrypto.sign_transaction(
    #     iroha.transaction([iroha.command('CreateAsset', asset_name=coin_name, domain_id=domain_name, precision=2)]), ADMIN_PRIVATE_KEY)
    # send_transaction_and_print_status(net, tx)

    create_user(iroha, net, domain_name, 'user99', ADMIN_PRIVATE_KEY)


def main(argv):
    """
    Main function.
    """
    
    if sys.version_info[0] < 3:
        raise Exception('Python 3 or a more recent version is required.')

    
    ROLE = os.getenv('ROLE', 'admin')
    if ROLE == 'admin':
        init_admin()
    

if __name__ == '__main__':
    app.run(main)