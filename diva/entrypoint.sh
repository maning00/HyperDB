#!/usr/bin/env bash
#
# Copyright (C) 2020 diva.exchange
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Author/Maintainer: Konrad Bächler <konrad@diva.exchange>
#

LOG_LEVEL=${LOG_LEVEL:-"trace"}

# wait for postgres
IP_POSTGRES=${IP_POSTGRES:?Error: environment variable IP_POSTGRES undefined}
PORT_POSTGRES=${PORT_POSTGRES:-5432}
/wait-for-it.sh ${IP_POSTGRES}:${PORT_POSTGRES} -t 30 || exit 1
sleep 10

IP_HTTP_PROXY=${IP_HTTP_PROXY:-} # like 172.20.101.200
PORT_HTTP_PROXY=${PORT_HTTP_PROXY:-} # like 4444
NO_PROXY=${NO_PROXY:-}
if [[ ${IP_HTTP_PROXY} = 'bridge' && PORT_HTTP_PROXY != "" ]]
then
  IP_HTTP_PROXY=`ip route | awk '/default/ { print $3 }'`
fi

if [[ -f /opt/iroha/data/blockchain.network ]]
then
  BLOCKCHAIN_NETWORK=$(</opt/iroha/data/blockchain.network)
else
  BLOCKCHAIN_NETWORK=${BLOCKCHAIN_NETWORK:-testnet_`pwgen -s -A -0 16 1`}
fi
echo ${BLOCKCHAIN_NETWORK} >/opt/iroha/data/blockchain.network

if [[ -f /opt/iroha/data/name.peer ]]
then
  NAME_PEER=$(</opt/iroha/data/name.peer)
else
  NAME_PEER=${NAME_PEER:-`pwgen -s -A -0 1 1``pwgen -s -A 14 1``pwgen -s -A -0 1 1`}
fi

# create a new peer key pair, if not available
if [[ ! -f /opt/iroha/data/${NAME_PEER}.priv || ! -f /opt/iroha/data/${NAME_PEER}.pub ]]
then
  cd /opt/iroha/data/
  /usr/bin/iroha-cli --account_name ${NAME_PEER} --new_account
  cd /opt/iroha/
  chmod 0644 /opt/iroha/data/${NAME_PEER}.*
fi
NAME_ACCOUNT=${NAME_PEER}@${BLOCKCHAIN_NETWORK}
if [[ ! -f /opt/iroha/data/${NAME_ACCOUNT}.priv || ! -f /opt/iroha/data/${NAME_ACCOUNT}.pub ]]
then
  cp /opt/iroha/data/${NAME_PEER}.priv /opt/iroha/data/${NAME_ACCOUNT}.priv
  cp /opt/iroha/data/${NAME_PEER}.pub /opt/iroha/data/${NAME_ACCOUNT}.pub
fi
PUB_KEY=$(</opt/iroha/data/${NAME_PEER}.pub)
echo ${NAME_PEER} >/opt/iroha/data/name.peer

# networking configuration, disable DNS
cat </resolv.conf >/etc/resolv.conf
cat </dnsmasq.conf >/etc/dnsmasq.conf
dnsmasq \
  --listen-address=127.0.1.1 \
  --no-resolv \
  --no-poll \
  --domain-needed \
  --local-service \
  --address=/#/127.0.0.0

# copy the configuration file
cp -r /opt/iroha/data/config-DEFAULT.json /opt/iroha/data/config.json

# set the postgres database name and its IP
if [[ ! -f /opt/iroha/data/diva-iroha-database ]]
then
  NAME_DATABASE=${NAME_DATABASE:-iroha}  # diva_`pwgen -A -0 16 1`
  echo ${NAME_DATABASE} >/opt/iroha/data/diva-iroha-database
fi
NAME_DATABASE=$(</opt/iroha/data/diva-iroha-database)
sed -i "s!\$IROHA_DATABASE!"${NAME_DATABASE}"!g" /opt/iroha/data/config.json
sed -i "s!\$IP_POSTGRES!"${IP_POSTGRES}"!g"  /opt/iroha/data/config.json
sed -i "s!\$LOG_LEVEL!"${LOG_LEVEL}"!g"  /opt/iroha/data/config.json

echo "Blockchain network: ${BLOCKCHAIN_NETWORK}"
echo "Iroha node: ${NAME_PEER}"

# check for a blockstore package to import
[[ -d /opt/iroha/import/ ]] || mkdir -p /opt/iroha/import/ && chmod a+rwx /opt/iroha/import/
[[ -d /opt/iroha/export/ ]] || mkdir -p /opt/iroha/export/
if [[ -f /opt/iroha/import/blockstore.tar.xz ]]
then
  tar -xf /opt/iroha/import/blockstore.tar.xz --directory /opt/iroha/blockstore/
  rm /opt/iroha/import/blockstore.tar.xz
fi

# check for the genesis block
if [[ ! -f /opt/iroha/blockstore/0000000000000001 ]]
then
  if [[ ! -f /opt/iroha/data/${BLOCKCHAIN_NETWORK}/0000000000000001 ]]
  then
    echo "Initialization: using local genesis"
    cp -p /opt/iroha/data/local-genesis/0000000000000001 /opt/iroha/blockstore/0000000000000001
  else
    echo "Initialization: using genesis from ${BLOCKCHAIN_NETWORK}"
    cp -p /opt/iroha/data/${BLOCKCHAIN_NETWORK}/0000000000000001 /opt/iroha/blockstore/0000000000000001
  fi
fi

# start the Iroha Blockchain
if [[ ${NO_PROXY} != "" ]]
then
  export no_proxy=${NO_PROXY}
  echo "No Proxy: ${no_proxy}"
fi
if [[ ${IP_HTTP_PROXY} != "" && ${PORT_HTTP_PROXY} != "" ]]
then
  export http_proxy=http://${IP_HTTP_PROXY}:${PORT_HTTP_PROXY}
  echo "HTTP Proxy: ${http_proxy}"
fi
cd /opt/iroha/data/
if [[ -f /opt/iroha/import/reuse_state ]]
then
  rm -f /opt/iroha/import/reuse_state
  echo "Reusing state..."
  /usr/bin/irohad --config config.json --keypair_name ${NAME_PEER} --reuse_state 2>&1 &
else
  /usr/bin/irohad --config config.json --keypair_name ${NAME_PEER} --drop_state 2>&1 &
  touch /opt/iroha/import/reuse_state
fi
cd /opt/iroha/

# catch SIGINT and SIGTERM
trap "touch /opt/iroha/import/sigterm" SIGTERM SIGINT

# main loop, pack and export blockchain, if changed
MTIME_BS=0
COUNT_EXPORT=0
while [[ `pgrep -c irohad` -gt 0 && ! -f /opt/iroha/import/sigterm ]]
do
  sleep 2

  if [[ -f /opt/iroha/import/createuser ]]
  then
    NAME_ACCOUNT_NEW=$(</opt/iroha/import/createuser)
    rm /opt/iroha/import/createuser
    cd /opt/iroha/data/
    /usr/bin/iroha-cli --account_name ${NAME_ACCOUNT_NEW} --new_account
    cd /opt/iroha/
    chmod 0644 /opt/iroha/data/${NAME_ACCOUNT_NEW}.*
  fi

  if [[ -f /opt/iroha/import/createexport ]]
  then
    rm /opt/iroha/import/createexport
    T_BS=`stat -c %Y /opt/iroha/blockstore`
    if [[ ${MTIME_BS} != ${T_BS} ]]
    then
      MTIME_BS=${T_BS}
      ls -1t /opt/iroha/blockstore/ >/opt/iroha/export/lst
      rm -f /opt/iroha/export/blockstore.tar.xz

      tar -c -J -f /opt/iroha/export/blockstore.tar.xz \
        --directory /opt/iroha/blockstore/ \
        --verbatim-files-from --files-from=/opt/iroha/export/lst

      rm -f /opt/iroha/export/lst
    fi
  fi
done

# clean up
rm -f /opt/iroha/import/sigterm
pkill -SIGTERM irohad
t=0
while [[ ${t} < 10 && `pgrep -c irohad` -gt 0 ]]
do
  ((t+=1))
  sleep 5
done
[[ `pgrep -c irohad` -gt 0 ]] && pkill -SIGKILL irohad && sleep 5
