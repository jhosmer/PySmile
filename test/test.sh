#!/bin/bash -eu

BASE=$(dirname $0)/..

function test_file() {
    local smile_file=$1
    local json_file=$2
    echo "*** C *** Testing $smile_file"
    ${BASE}/build/Release/unsmile ${BASE}/test/data/smile/${smile_file} | diff -du ${BASE}/test/data/json/${json_file} -
}

for i in 1 2 3 4 5; do
    test_file json-org-sample${i}.smile json-org-sample${i}.jsn
done

for i in 4k 64k; do
  test_file numbers-int-${i}.smile numbers-int-${i}.jsn
done

for i in 1 2; do
    test_file test${i}.smile test${i}.jsn
done