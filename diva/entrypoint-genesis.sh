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

# -e  Exit immediately if a simple command exits with a non-zero status
set -e

/wait-for-it.sh postgres_genesis:5432 -t 30

# re-creating all testnet keys
iroha-cli -new_account -account_name diva@testnet.diva.i2p
iroha-cli -new_account -account_name n1
iroha-cli -new_account -account_name n2
iroha-cli -new_account -account_name n3
iroha-cli -new_account -account_name n4
iroha-cli -new_account -account_name n5
iroha-cli -new_account -account_name n6
iroha-cli -new_account -account_name n7
iroha-cli -new_account -account_name genesis-node

DIVA_TESTNET=$(<diva@testnet.diva.i2p.pub)
N1=$(<n1.pub)
N2=$(<n2.pub)
N3=$(<n3.pub)
N4=$(<n4.pub)
N5=$(<n5.pub)
N6=$(<n6.pub)
N7=$(<n7.pub)

# replace the key values in the genesis.block setup
sed -i 's!\$DIVA_TESTNET!'"${DIVA_TESTNET}"'!g' genesis.block
sed -i 's!\$N1!'"${N1}"'!g' genesis.block
sed -i 's!\$N2!'"${N2}"'!g' genesis.block
sed -i 's!\$N3!'"${N3}"'!g' genesis.block
sed -i 's!\$N4!'"${N4}"'!g' genesis.block
sed -i 's!\$N5!'"${N5}"'!g' genesis.block
sed -i 's!\$N6!'"${N6}"'!g' genesis.block
sed -i 's!\$N7!'"${N7}"'!g' genesis.block

# create the genesis block
irohad \
  --drop_state \
  --overwrite_ledger \
  --genesis_block genesis.block \
  --config config-genesis.json \
  --keypair_name genesis-node
