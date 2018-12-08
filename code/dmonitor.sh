#!/bin/bash
#Script tracking last debug log

LAST_LOG=$(ls -1t log/debug.* | head -n1)
echo $LAST_LOG
head -n1 $LAST_LOG && tail -f $LAST_LOG
