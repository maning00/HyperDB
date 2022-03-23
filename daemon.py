from iroha import Iroha, IrohaGrpc
from utils import *


class Daemon:
    """
    chaindb daemon.
    """

    def __init__(self, FLAGS, keypair):
        self.iroha = Iroha(FLAGS.account_id)
        self.net = IrohaGrpc('{}:{}'.format(
            FLAGS.iroha_addr, FLAGS.iroha_port))
        self.domain = FLAGS.account_id.split('@')[1]
        self.keypair = keypair
        self.account_id = FLAGS.account_id


    def send_transaction_and_print_status(self, transaction):
        """
        Sends a transaction to the Iroha network and prints its status.
        """
        hex_hash = binascii.hexlify(IrohaCrypto.hash(transaction))
        logging.info('Transaction hash = %s, creator = %s', hex_hash,
                     transaction.payload.reduced_payload.creator_account_id)
        self.net.send_tx(transaction)
        for status in self.net.tx_status_stream(transaction):
            logging.info(status)


    @trace
    def create_user(self, user_name) -> Keypair:
        """
        Creates a user.
        """
        user_private_key = IrohaCrypto.private_key()
        user_public_key = IrohaCrypto.derive_public_key(user_private_key)

        tx = self.iroha.transaction([
            self.iroha.command('CreateAccount', account_name=user_name, domain_id=self.domain,
                          public_key=user_public_key)
        ])
        IrohaCrypto.sign_transaction(tx, self.keypair.private_key)
        self.send_transaction_and_print_status(tx)
        return Keypair(user_private_key, user_public_key)


    @trace
    def create_asset(self, asset_name, precision):
        """
        Creates an asset.
        asset_name: name string
        precision: number of decimal places
        """
        tx = self.iroha.transaction([
            self.iroha.command('CreateAsset', asset_name=asset_name, domain_id=self.domain, precision=precision)
        ])
        IrohaCrypto.sign_transaction(tx, self.keypair.private_key)
        self.send_transaction_and_print_status(tx)

    
    @trace
    def add_asset(self, asset_id, amount):
        """
        Adds an asset to an account.
        asset_id: asset#domain
        amount: number of assets
        """
        tx = self.iroha.transaction([
            self.iroha.command('AddAssetQuantity', asset_id=asset_id, amount=str(amount))
        ])
        IrohaCrypto.sign_transaction(tx, self.keypair.private_key)
        self.send_transaction_and_print_status(tx)

    
    @trace
    def transfer_asset(self, asset_id, amount, dest_account_id):
        """
        Transfers an asset from an account to another.
        asset_id: asset#domain
        amount: number of assets
        dest_account_id: account@domain
        """
        tx = self.iroha.transaction([
            self.iroha.command('TransferAsset', src_account_id=self.account_id, dest_account_id=dest_account_id,
                          asset_id=asset_id, amount=str(amount))
        ])
        IrohaCrypto.sign_transaction(tx, self.keypair.private_key)
        self.send_transaction_and_print_status(tx)


    @trace
    def set_kvstore(self, key, value, account_id = None):
        """
        Sets a key-value pair in the kvstore.
        """
        if account_id is None:
            account_id = self.account_id
        tx = self.iroha.transaction([
            self.iroha.command('SetAccountDetail', account_id=account_id, key=key, value=value)
        ])
        IrohaCrypto.sign_transaction(tx, self.keypair.private_key)
        self.send_transaction_and_print_status(tx)

    
    @trace
    def get_kvstore(self, key, account_id = None):
        """
        Gets a key-value pair from the kvstore.
        """
        if account_id is None:
            account_id = self.account_id
        query = self.iroha.query('GetAccountDetail', account_id=account_id)
        IrohaCrypto.sign_query(query, self.keypair.private_key)
        response = self.net.send_query(query)
        data = response.account_detail_response
        print(data)

    
    @trace
    def get_account_assets(self, account_id):
        """
        Gets the assets of an account.
        """
        query = self.iroha.query('GetAccountAssets', account_id=account_id)
        IrohaCrypto.sign_query(query, self.keypair.private_key)
        response = self.net.send_query(query)
        data = response.account_assets_response
        print(data)


