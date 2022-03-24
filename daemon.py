from iroha import Iroha, IrohaGrpc
import psycopg
import json, base64
from psycopg.rows import class_row
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
        self.set_id = 1
        self.get_id = 1

        logging.info('Connecting to PostgresSQL...')
        self.db_conn = psycopg.connect("host='127.0.0.1' dbname='chaindb' user='postgres' password='mysecretpassword'")
        logging.info('Connected to PostgresSQL.')
        print("account_id is {}".format(self.account_id))



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
            if (status[2] != 0):
                logging.error('Transaction returned status %s', status[2])
                return False
        return True


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
        logging.info('Setting kvstore key %s to value %s', key, value)
        if account_id is None:
            account_id = self.account_id
        tx = self.iroha.transaction([
            self.iroha.command('SetAccountDetail', account_id=account_id, key=key, value=value)
        ])
        IrohaCrypto.sign_transaction(tx, self.keypair.private_key)
        return self.send_transaction_and_print_status(tx)

    
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

    
    def show_all_tables(self):
        with self.db_conn.cursor() as cur:
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'")
            res = {'result':[]}
            for row in cur.fetchall():
                res['result'].append(row[0])
            return res


    def create_table(self, table_name):
        with self.db_conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE "{}" (id SERIAL NOT NULL PRIMARY KEY, name VARCHAR(255) NOT NULL, timestamp INT NOT NULL,
            author VARCHAR(255) NOT NULL, email VARCHAR(255) NOT NULL, 
            institution VARCHAR(255) NOT NULL, environment TEXT NOT NULL, 
            parameters TEXT NOT NULL, details TEXT NOT NULL, attachment TEXT NOT NULL,
            hash TEXT NOT NULL)
            """.format(table_name))
            self.db_conn.commit()


    def insert_data(self, entry):
        with self.db_conn.cursor() as cur:
            hash = entry.cal_hash()
            cur.execute("""
            INSERT INTO "{}" (name, timestamp, author, email, institution, environment, parameters, details, attachment, hash)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """.format(self.account_id), (entry.name, entry.timestamp, entry.author, entry.email, entry.institution, entry.environment, entry.parameters, entry.details, entry.attachment, hash))

            log = {}
            log['name'] = entry.name
            log['timestamp'] = entry.timestamp
            log['hash'] = hash
            if self.set_kvstore('set_'+str(self.set_id), base64.b16encode(json.dumps(log).encode('utf8'))) == False:
                logging.error('set_kvstore failed')
                return False
            self.set_id+=1
            self.db_conn.commit()
            return True


    def get_data(self, table_name):
        """
        Gets the data from the database.
        """
        with self.db_conn.cursor(row_factory=class_row(Entry)) as cur:
            op_str = 'SELECT name, timestamp, author, email, institution, environment, parameters, details, attachment, hash FROM "{}"'.format(table_name)
            cur.execute(op_str)
            
            self.set_kvstore('get_'+str(self.get_id), op_str)
            self.get_id+=1
            res = []
            for row in cur.fetchall():
                res.append(row.__dict__)
        print("returned {}".format(res))
        return res
