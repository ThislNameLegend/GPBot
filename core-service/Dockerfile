FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    curl \
    libcurl4-openssl-dev \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY CMakeLists.txt .
COPY include/ ./include/

RUN git clone https://github.com/yhirose/cpp-httplib.git /tmp/httplib && \
    cp /tmp/httplib/httplib.h /usr/local/include/ && \
    git clone https://github.com/nlohmann/json.git /tmp/json && \
    cp -r /tmp/json/include/nlohmann /usr/local/include/

COPY src/ ./src/

RUN mkdir -p build && cd build && \
    cmake .. && \
    make

EXPOSE 8080

CMD ["./build/core_service"]
