#!/bin/bash
DATE=$(date +%s)
#cd ..
docker pull philipsahli/centos:latest
rm -rf build &&  mkdir -p build
tar -cf - --exclude build . | tar -xf - -C build/
cd build/
mv Dockerfile-worker Dockerfile
sed -i s/cachebust_]*/cachebust_"$DATE"/g Dockerfile
docker build -t philipsahli/tumbo-worker:develop .
cd ..
rm -rf build
