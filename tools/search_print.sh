#!/bin/sh
egrep --exclude=config.py --exclude-dir=.git --exclude-dir=tools -Ir "([	]+|^)print " . --color=auto
