#!/bin/bash

LIB=~/Documents/Arduino/libraries/CSE474/

mkdir -p $LIB
rm -rf $LIB/*
cp lib/*.h $LIB/
