FROM python:3.10-alpine AS builder

# Install build‑time dependencies (only needed for compiling wheels)
# – gcc, musl-dev, libffi-dev, etc.  These will be removed later.
RUN apk add --no-cache \
        gcc \
        musl-dev \
        libffi-dev \
        python3-dev

ARG USER=appuser
ARG UID=1000
RUN adduser \
        --disabled-password \
        --gecos "" \
        --home /app \
        --uid "${UID}" \
        "${USER}"

WORKDIR /app

# Copy the current directory contents into the container at /app
COPY main.py config.py requirements.txt /app
COPY utils/ /app/utils/
COPY patchedPypresence/ /app/patchedPypresence/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

USER ${USER}

FROM python:3.10-alpine AS runtime

# Re‑create the same non‑root user in the final stage
ARG USER=appuser
ARG UID=1000
RUN adduser \
        --disabled-password \
        --gecos "" \
        --home /app \
        --uid "${UID}" \
        "${USER}"

WORKDIR /app

# Copy the installed site‑packages and our app files from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /app /app

# Ensure the user owns the copied files (optional – usually fine)
RUN chown -R ${UID}:${UID} /app

USER ${USER}

# Run main.py and keep the container running
CMD ["sh", "-c", "python -X utf8 main.py & tail -f /dev/null"]
