#!/bin/bash

mode=patch
VERSION=$(bumpversion --dry-run --list patch|egrep new_version|awk -F= '{print $2}')
git checkout -b $VERSION
bumpversion patch
git push --tags
git push
