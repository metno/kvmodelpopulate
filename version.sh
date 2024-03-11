#! /bin/bash

grep "version *= *" setup.py | sed  "s/.*version *= *\"\(.*\)\".*/\1/"
