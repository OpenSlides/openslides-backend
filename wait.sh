#!/bin/sh

while ! nc -z "$1" "$2"; do
    echo "waiting for $1:$2"
    sleep 1
done

echo "$1:$2 is available"
