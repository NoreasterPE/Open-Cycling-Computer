#!/bin/bash

LAST_LOG=$(ls -1r log/debug.* | head -n1)
echo Last log $LAST_LOG
head -n1 $LAST_LOG && tail -f $LAST_LOG
