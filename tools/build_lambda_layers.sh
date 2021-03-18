#!/bin/bash

rm -rf "../build"
mkdir "../build"

mkdir "../build/middleware_layer"
mkdir "../build/middleware_layer/python"
cp -r "../backend/middleware" "../build/middleware_layer/python"

mkdir "../build/vendor_layer"
mkdir "../build/vendor_layer/python"
pipenv lock -r | grep "pydantic" > "../build/vendor.txt"
pip install -r "../build/vendor.txt" -t "../build/vendor_layer/python"
