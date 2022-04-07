import base64
import json
import pickle
import sys
import threading

import binascii
from turtle import distance
import psycopg
from iroha import Iroha, IrohaGrpc
from psycopg.rows import class_row

from skiplist import SkipList
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
        self.skip_list = SkipList()
        self.account_id = FLAGS.account_id
        self.set_id = 1
        self.offsets = []
        self.is_syncing = False

        # connect to the database
        logging.info('Connecting to PostgresSQL...')
        try:
            self.db_conn = psycopg.connect(
                "host='172.29.101.25' dbname='chaindb' user='iroha' password='iroha'")
        except:
            logging.warning("Cannot find database, tring to create one...")
            con = psycopg.connect(
                "host='172.29.101.25' user='iroha' password='iroha'")
            con._set_autocommit(True)
            cursor = con.cursor()
            cursor.execute("create database chaindb")
            con.commit()

            try:
                self.db_conn = psycopg.connect(
                    "host='172.29.101.25' dbname='chaindb' user='iroha' password='iroha'")
            except:
                logging.error("Cannot connect to database")
                sys.exit(1)
            self.create_table(self.account_id)

        logging.info('Connected to PostgresSQL.')
        if self.account_id not in self.show_all_tables()['result']:
            self.create_table(self.account_id)

        self.syn_db_data()
        self.check_duplication()
        logging.info(
            "Account ID is {}\n Daemon is running...".format(self.account_id))
        

    def syn_db_data(self):
        # get most recent set_id from the database
        self.is_syncing = True
        with self.db_conn.cursor() as cur:
            cur.execute('SELECT MAX(id) FROM "{}"'.format(self.account_id))
            res = cur.fetchone()
            if res[0] is not None:
                self.set_id = res[0] + 1
                logging.info("Getting latest data...")
                val = self.get_kvstore('set_' + str(self.set_id))
                while(val):
                    entry = pickle.loads(base64.b16decode(val))
                    self.insert_data(entry, False)
                    self.set_id += 1
                    val = self.get_kvstore('set_' + str(self.set_id))

                for i in range(1, self.set_id):
                    cur.execute('SELECT hash FROM "{}" WHERE id=%s'.format(
                        self.account_id), (str(i),))
                    res = cur.fetchone()
                    if res is not None:
                        self.skip_list.update(True, binascii.a2b_hex(res[0]))
        i = 0
        id_val = self.get_kvstore('offset_' + str(i))
        while(id_val != None):
            self.offsets.append(int(id_val))
            i += 1
            id_val = self.get_kvstore('offset_' + str(i))
        
        threading.Timer(60, self.syn_db_data).start()
        self.is_syncing = False


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
        if self.send_transaction_and_print_status(tx):
            return Keypair(user_private_key, user_public_key)
        return None

    @trace
    def create_asset(self, asset_name, precision) -> bool:
        """
        Creates an asset.
        asset_name: name string
        precision: number of decimal places
        """
        tx = self.iroha.transaction([
            self.iroha.command('CreateAsset', asset_name=asset_name,
                               domain_id=self.domain, precision=precision)
        ])
        IrohaCrypto.sign_transaction(tx, self.keypair.private_key)
        return self.send_transaction_and_print_status(tx)

    @trace
    def add_asset(self, asset_id, amount) -> bool:
        """
        Adds an asset to an account.
        asset_id: asset#domain
        amount: number of assets
        """
        tx = self.iroha.transaction([
            self.iroha.command('AddAssetQuantity',
                               asset_id=asset_id, amount=str(amount))
        ])
        IrohaCrypto.sign_transaction(tx, self.keypair.private_key)
        return self.send_transaction_and_print_status(tx)

    @trace
    def transfer_asset(self, asset_id, amount, dest_account_id) -> bool:
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
        return self.send_transaction_and_print_status(tx)

    @trace
    def set_kvstore(self, key, value, account_id=None) -> bool:
        """
        Sets a key-value pair in the kvstore.
        """
        logging.info('Setting kvstore key %s to value %s', key, value)
        if account_id is None:
            account_id = self.account_id
        tx = self.iroha.transaction([
            self.iroha.command('SetAccountDetail',
                               account_id=account_id, key=key, value=value)
        ])
        IrohaCrypto.sign_transaction(tx, self.keypair.private_key)
        return self.send_transaction_and_print_status(tx)

    def get_kvstore(self, key, account_id=None):
        """
        Gets a key-value pair from the kvstore.
        """
        if account_id is None:
            account_id = self.account_id
        query = self.iroha.query(
            'GetAccountDetail', account_id=account_id, key=key)
        IrohaCrypto.sign_query(query, self.keypair.private_key)
        response = self.net.send_query(query)
        data = json.loads(response.account_detail_response.detail)
        if len(data) == 0:
            logging.debug('Key %s not found', key)
            return None
        else:
            logging.debug('Key %s has value %s', key, data[account_id][key])
            return data[account_id][key]

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
            cur.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'")
            res = {'result': []}
            for row in cur.fetchall():
                res['result'].append(row[0])
            return res

    def create_table(self, table_name):
        logging.debug('Creating table %s', table_name)
        with self.db_conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE "{}" (id INT NOT NULL PRIMARY KEY, name VARCHAR(255) NOT NULL, timestamp INT NOT NULL,
            author VARCHAR(255) NOT NULL, email VARCHAR(255) NOT NULL, 
            institution VARCHAR(255) NOT NULL, environment TEXT NOT NULL, 
            parameters TEXT NOT NULL, details TEXT NOT NULL, attachment TEXT NOT NULL,
            hash TEXT NOT NULL, index_offset INT NOT NULL, creator VARCHAR NOT NULL, reserved TEXT NULL)
            """.format(table_name))
            self.db_conn.commit()

    def insert_data(self, entry, set_kvstore=True):
        with self.db_conn.cursor() as cur:
            hash = entry.cal_hash()
            offset = entry.offset
            # if offset is set, it means that it is a edit request
            if entry.offset == -1:
                offset = self.set_id - 1

            if offset >= len(self.offsets):
                self.offsets.append(offset)
            self.offsets[offset] = self.set_id

            cur.execute("""
            INSERT INTO "{}" VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NULL)
            """.format(self.account_id), (
                self.set_id, entry.name, entry.timestamp, entry.author, entry.email, entry.institution, entry.environment,
                entry.parameters, entry.details, entry.attachment, hash.hexdigest(), offset, self.account_id))

            if set_kvstore:
                if self.set_kvstore('set_' + str(self.set_id), base64.b16encode(pickle.dumps(entry))) == False:
                    logging.error('set_kvstore failed')
                    return False

                if self.set_kvstore('offset_' + str(offset), str(self.set_id)) == False:
                    logging.error('set_kvstore failed')
                    return False

            self.skip_list.update(True, hash.digest())
            logging.debug('inserting {}'.format(hash.digest()))
            self.set_id += 1
            self.db_conn.commit()
            return True

    def get_data(self, table_name):
        """
        Gets the data from the database.
        """
        with self.db_conn.cursor() as cur:
            op_str = 'SELECT * FROM "{}"'.format(
                table_name)
            cur.execute(op_str)
            if table_name != self.account_id:
                self.transfer_asset('coin#' + self.domain, 1, table_name)
            res = []
            for row in cur.fetchall():
                line = {}
                en = Entry.from_tuple(row)
                if (en.id == self.offsets[en.offset]): # always return the latest version of the entry
                    line['data'] = en.__dict__
                    # res.append(row.__dict__)
                    logging.debug('verifying {}'.format(en.hash))
                    response = self.skip_list.verify(binascii.a2b_hex(en.hash))
                    line['authentication'] = response.__dict__
                    res.append(line)
        return res

    def check_duplication(self):
        with self.db_conn.cursor() as cur:
            op_str = 'SELECT * FROM "{}"'.format(
                self.account_id)
            cur.execute(op_str)
            res = []
            for row in cur.fetchall():
                en = Entry.from_tuple(row)
                if (en.id == self.offsets[en.offset]):
                    en.simhash = en.cal_simhash()
                    res.append(en)
            
            for i in range(len(res)):
                for j in range(i+1, len(res)):
                    distance = res[i].simhash.distance(res[j].simhash)
                    if distance > 8:
                        logging.debug('Duplicate entry found({}): {} and {}'.format(distance, res[i].name, res[j].name))
        threading.Timer(600, self.check_duplication).start()

    def select_columns(self, table_name, column_names):
        """
        Selects columns from the database.
        """
        with self.db_conn.cursor() as cur:
            op_str = 'SELECT '
            for i in range(len(column_names)):
                op_str += column_names[i]
                if i != len(column_names) - 1:
                    op_str += ', '
            op_str += ' FROM "{}"'.format(table_name)
            cur.execute(op_str)
            res = []
            for row in cur.fetchall():
                res.append(row)
        return res

    def delete_data(self, table_name, hash):
        """
        Deletes data from the database.
        """
        with self.db_conn.cursor() as cur:
            cur.execute(
                "DELETE FROM {} WHERE hash=%s".format(table_name), hash)
            self.db_conn.commit()
            self.set_kvstore('del_' + str(self.del_id), table_name)
            return True
