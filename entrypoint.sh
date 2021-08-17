#!/bin/sh -l

poetry install --no-dev
poetry shell

poetry run python -m shhhhh.policy1 $1
