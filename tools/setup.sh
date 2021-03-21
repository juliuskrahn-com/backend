#!/bin/bash
# run in project root dir

rm -rf "build/"
mkdir "build/"

mkdir -p "build/middleware_layer/python/backend"
cp -r "backend/middleware" "build/middleware_layer/python/backend"

mkdir -p "build/vendor_layer/python"
pydantic="$(grep "pydantic" requirements.txt)"
pip install "$pydantic" -t build/vendor_layer/python

pip install -r requirements.txt
