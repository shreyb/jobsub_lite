#!/bin/bash 
od -c /bin/* | head -c $1
od -c /bin/* | head -c $1  1>&2

