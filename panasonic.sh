#!/bin/bash -x

source /usr/share/taiseia101/bin/activate
cd /usr/share/taiseia101/src
python panasonic_fy24cxw.py /dev/ttyUSB0
