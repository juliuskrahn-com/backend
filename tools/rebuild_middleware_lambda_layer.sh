#!/bin/bash

rm -rf "../build/middleware_layer"
mkdir "../build/middleware_layer"
mkdir "../build/middleware_layer/python"
mkdir "../build/middleware_layer/python/backend"
cp -r "../backend/middleware" "../build/middleware_layer/python/backend"
