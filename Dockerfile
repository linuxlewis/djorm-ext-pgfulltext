FROM ubuntu:14.04

MAINTAINER Rémy Greinhofer <remy.greinhofer@livelovely.com>

# Create the directory containing the code.
RUN mkdir /code
WORKDIR /code

# Set the environment variables.
ENV PYTHONPATH $PYTHONPATH:/code

# Update the package list.
RUN apt-get update \

  # Install libgeos.
  && DEBIAN_FRONTEND=noninteractive apt-get install -y \
  # Install Python3.
    python3 \
    python3-dev \
    python3-pip \

  # Install postgresql dev lib.
    libpq-dev \

  # Cleaning up.
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy the requirements.txt file.
COPY requirements.txt /code/requirements.txt
COPY test-requirements.txt /code/test-requirements.txt

# Install the pip packages.
RUN pip3 install -q -r requirements.txt -r test-requirements.txt
