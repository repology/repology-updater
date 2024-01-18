ARG POSTGRES_VERSION=15
FROM postgres:${POSTGRES_VERSION}

ARG POSTGRES_VERSION

RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    pkg-config \
    postgresql-server-dev-${POSTGRES_VERSION} \
    cmake

# Install libversion
RUN git clone https://github.com/repology/libversion.git && \
    cd libversion && \
    cmake -S . -B build && \
    cmake --build build && \
    cmake --install build

# Install postgresql-libversion
RUN git clone https://github.com/repology/postgresql-libversion.git && \
    cd postgresql-libversion && \
    make && \
    make install

# FIXME: This is probably a bug in the Makefile
RUN ln -s libversion.so /usr/lib/postgresql/${POSTGRES_VERSION}/lib/libversion.so.1

# Add the built libraries to LD_LIBRARY_PATH
RUN ldconfig /usr/lib/postgresql/${POSTGRES_VERSION}/lib && \
    ldconfig /usr/local/libs

CMD ["postgres"]
