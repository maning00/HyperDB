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

TAG=${TAG:-1.2.1}
THREADS=${THREADS:-4}

# removing iroha and vcpkg
rm -Rf iroha
rm -Rf vcpkg

echo "Cloning: git clone --depth 1 --branch $TAG https://github.com/hyperledger/iroha.git"
git clone --depth 1 --branch $TAG https://github.com/hyperledger/iroha.git

iroha/vcpkg/build_iroha_deps.sh
vcpkg/bootstrap-vcpkg.sh -disableMetrics
vcpkg/vcpkg integrate install
cd iroha
cmake -H. -Bbuild -DTESTING=OFF -DCMAKE_TOOLCHAIN_FILE=/root/vcpkg/scripts/buildsystems/vcpkg.cmake -G "Ninja"
cmake --build build --target all -- -j${THREADS}

cp /root/iroha/build/bin/* /root/
strip -o /root/iroha-cli-stripped /root/iroha-cli
strip -o /root/irohad-stripped /root/irohad


