# Container image that runs your code
FROM python:3.9-slim

# RUN pip install -U pip
RUN pip install poetry
COPY poetry.lock poetry.lock
COPY pyproject.toml pyproject.toml

# Copies your code file from your action repository to the filesystem path `/` of the container
COPY entrypoint.sh /entrypoint.sh
COPY shhhhh shhhhh
RUN poetry install --no-dev

# Code file to execute when the docker container starts up (`entrypoint.sh`)
ENTRYPOINT ["/entrypoint.sh"]
