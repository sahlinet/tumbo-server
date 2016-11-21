#!/bin/bash

#../../compose2kube/compose2kube -compose-file-path ../../tumbo-sahli-net/ -output-dir k8s

sed -e 's/  namespace: .*/  namespace: tumbo/' -i *.yml

sed '/ExternalName/d' -i *yml

echo "apiVersion: v1" > all.yml
echo "kind: List" >> all.yml
echo "items:" >> all.yml

for i in $(ls -1 *yml|egrep -v all); do
    printf "-" >> all.yml
    cat $i | awk '{if ($0 == "apiVersion: v1") print "   " $0; else print "    " $0 }' >> all.yml
done
