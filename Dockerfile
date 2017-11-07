FROM python:3.6

WORKDIR /usr/src/app

COPY . /usr/src/app
VOLUME /usr/src/app

# Get all system-level deps
RUN apt update && \
    apt install -y cmake librpm-dev pkg-config

RUN pip install -r requirements.txt

# Install libversion
# and compile the python binding for it
RUN wget -qO- https://github.com/repology/libversion/archive/2.2.0.tar.gz | tar -xzf- && \
 ( cd libversion-2.2.0 && cmake . && make && make install ) && \
 make

ENTRYPOINT ./repology-app.py
