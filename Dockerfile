FROM python:3.9

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
      python3-pip \
      postgresql \
      postgresql-contrib \
      pkg-config \
      wget \
      yajl-tools \
      libyajl-dev \
      cmake \
      libpq-dev

WORKDIR /opt
RUN wget https://github.com/repology/libversion/archive/refs/tags/3.0.1.tar.gz && \
    tar -xzvf 3.0.1.tar.gz && \
    cd libversion-3.0.1 && \
    mkdir build && \
    cmake . && \
    cd build && \
    cmake --build ../ && \
    cd ../ && \
    make install && \
    ldconfig
    
WORKDIR /code
COPY . /code
RUN pip install -r requirements.txt && pip install -r requirements-dev.txt && \
    # import rpm required, not clear which is needed
    pip install rpm

