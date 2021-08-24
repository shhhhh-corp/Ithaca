#!/bin/bash -x

cd /                      # Github's actions/checkout@v2 is `cd`ing
                          # into /github/workspace (and deletes its
                          # contents)

echo "$GITHUB_EVENT_PATH"
cat "$GITHUB_EVENT_PATH"
python -m shhhhh.policies "$1" "$2"
