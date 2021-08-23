#!/bin/sh -l

poetry install --no-dev

poetry run python -m shhhhh.policy1 $1
