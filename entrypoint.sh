#!/bin/bash -x

cd /                      # Github's actions/checkout@v2 is `cd`ing
                          # into /github/workspace (and deletes its
                          # contents)

python -m shhhhh.policies $1 $2
