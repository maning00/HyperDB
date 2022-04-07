# HyperDB: A blockchain-based database
&emsp;&emsp;HyperDB is a blockchain database based on Hyperledger Iroha, mainly for experimental data copyright protection applications. <br>
&emsp;&emsp;In HyperDB, the transaction log is stored in the blockchain, and data is cached in the same PostgresSQL database as iroha. HyperDB provides a simple interface to query and update data. In addition, HyperDB uses authenticated data structure to organize data entries, enabling lightweight clients to perform fast data validation without having to download the full on-chain data for data validation.<br>
&emsp;&emsp;HyperDB can customize the genesis block and perform test network deployment through the Iroha rapid deployment script based on DIVA.EXCHANGE. See `diva` folder for more details.

## Usage
 - Start blockchain backend
    - Create custom genesis block and docker image from `diva` folder.
    - Run `docker-compose up -d` to start the blockchain backend.
 - Start HyperDB server
    - Run `python app.py` to start the HyperDB server. HyperDB server will be listening on port 5000, and can be accessed through HTTP API.

## HyperDB API
`/api/v1/get_all_table`: Get all tables in the database. If there is no table, return `[]`.
`/api/v1/create_table`: Create a new table with given name `data['table_name']`
`/api/v1/insert`: Insert data to the database.
`/api/v1/get_data`: Query data with specified `table_name`.
`/api/v1/select_columns`: Query data with specified column names.
`/api/v1/login`: User login.
`/api/v1/upload`: Upload file to IPFS, file must upload with multipart form.

## License
GPL-3.0