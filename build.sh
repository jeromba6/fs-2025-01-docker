#!/bin/bash

for image in static-webserver reverse-proxy
do
    pushd ${image}
    docker build -t $image:latest .
    popd
done