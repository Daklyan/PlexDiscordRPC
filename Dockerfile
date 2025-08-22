# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

ARG USER=appuser
ARG UID=1000
RUN adduser --uid ${UID} --disabled-password --gecos "" ${USER}
RUN chown -R ${USER}:${USER} /app

USER ${USER}

# Run main.py and keep the container running
CMD ["sh", "-c", "python -X utf8 main.py & tail -f /dev/null"]
