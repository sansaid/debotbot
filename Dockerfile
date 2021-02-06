FROM busybox:latest AS prep

# Create work directory
WORKDIR /app

# Move everything that's not in .dockerignore
ADD . .

# Convert all files to UNIX format just in case
RUN find /app/. -type f  | xargs dos2unix && \
    ls /app

#### NEXT STAGE ####
FROM python:3.9-alpine

WORKDIR /app
COPY --from=prep /app /app

# Install requirements
RUN python -m pip install --upgrade pip && \
    apk add --no-cache --virtual .pynacl_deps build-base gcc musl-dev python3-dev libffi-dev openssl-dev && \
    python -m pip install -r /app/requirements.txt && \
    ls /app

# Run bot
ENTRYPOINT [ "python", "/app/bot.py" ]