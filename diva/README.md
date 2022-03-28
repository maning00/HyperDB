# DIVA.EXCHANGE: Hyperledger/Iroha Blockchain

This is an open source project (AGPLv3 licensed) - transparently developed by the association [DIVA.EXCHANGE](https://diva.exchange).

All source code is available here: https://codeberg.org/diva.exchange/iroha/.

The blockchain backend of _diva_ is based on Hyperledger/Iroha. 

_Important:_ these instructions are suitable for a testnet in a development environment (not production). This project contains well-known private keys (so they are not private anymore). To understand the cryptography related to Iroha, read the docs: https://iroha.readthedocs.io/en/master/  

## Get Started

DIVA.EXCHANGE offers preconfigured packages to start or join the DIVA.EXCHANGE Iroha testnet.

Preconfigured packages are available as [diva-dockerized](https://codeberg.org/diva.exchange/diva-dockerized).

For advanced users on an operating system supporting Docker (Linux, Windows, MacOS) the following instructions will help to get started.

### Using Docker Compose

**IMPORTANT**: To start a local Iroha testnet, make sure you have [Docker Compose](https://docs.docker.com/compose/install/) installed. Check your Docker Compose installation by executing `docker-compose --version` in a terminal.

Clone the code repository from the public repository:
```
git clone -b main https://codeberg.org/diva.exchange/iroha.git
cd iroha
```

### Latest available release

If you have Docker Compose available, execute within your iroha folder:
```
sudo docker-compose up -d
```

By default this will use the configuration file `/docker-compose.yml`. Within this docker-compose configuration file a local iroha testnet gets defined. This also involves a network configuration. By default there are no ports explosed and the network is defined as "internal".

After start up five docker container will be running: a postgres container (postgres.diva.local), three iroha container (n1.diva.local, n2.diva.local and n3.diva.local) and an explorer container (explorer.diva.local).

Open your browser and visit the local blockchain explorer: http://172.29.101.3:3920.

The IP address of the explorer, "172.29.101.3", is defined within the docker compose configuration file, `/docker-compose.yml`. Set up your own local network configuration and use this configuration file as an example or starting point.

To stop the container using Docker Compose, execute:
```
sudo docker-compose down
```
 
To stop the container, including the removal of the related volumes (data of the containers gets removed, so the local blockchain gets deleted) using Docker Compose, execute:
```
sudo docker-compose down --volumes
```

## Build your Own Genesis Block

Make sure, the code is available by cloning the code repository from the public repository:
```
git clone -b main https://codeberg.org/diva.exchange/iroha.git
cd iroha
```

Within the folder `data-genesis` you can configure your own Genesis Block. Execute
```
sudo ./bin/genesis.sh
```
to create your own Genesis Block. Take a close look at the script to understand how the private keys are handled!

After building the Genesis Block, run your container using Docker Compose 
```
sudo docker-compose up -d
```

## Environment variables

Within the compose file (docker-compose.yml) some environment variables are used. They might be adapted to local needs.

### LOG_LEVEL
Set the iroha log level: trace, debug, info, warning, error, critical. Default: info.

### IP_POSTGRES
IP address of related postgres container. Mandatory. 

### PORT_POSTGRES
Port of the related postgres container. Default: 5432.

### NAME_DATABASE
Name of the iroha database to use. Defaults to "iroha". 

### BLOCKCHAIN_NETWORK
Name of the iroha blockchain network to run. Defaults to an empty string and gets therefore set automatically by the entrypoint script.

### NAME_PEER
Name of the iroha peer and the private/public key. Defaults to an empty string and gets therefore set automatically by the entrypoint script. 

### IP_HTTP_PROXY
IP address of the container running an HTTP proxy. Use it together for an I2P network.

### PORT_HTTP_PROXY
Port of the container running an HTTP proxy. Use it together for an I2P network.

### NO_PROXY
Comma separated list of domains to exclude from proxied traffic.

## Contact the Developers

On [DIVA.EXCHANGE](https://www.diva.exchange) you'll find various options to get in touch with the team. 

Talk to us via [Telegram](https://t.me/diva_exchange_chat_de) (English or German).

## Donations

Your donation goes entirely to the project. Your donation makes the development of DIVA.EXCHANGE faster.

XMR: 42QLvHvkc9bahHadQfEzuJJx4ZHnGhQzBXa8C9H3c472diEvVRzevwpN7VAUpCPePCiDhehH4BAWh8kYicoSxpusMmhfwgx

BTC: 3Ebuzhsbs6DrUQuwvMu722LhD8cNfhG1gs

Awesome, thank you!
