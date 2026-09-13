FROM nvidia/cuda:12.8.1-devel-ubuntu22.04 AS build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential cmake git libssl-dev ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY . .
RUN cmake -S . -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=86 -DGGML_NATIVE=OFF -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF -DLLAMA_BUILD_SERVER=ON -DLLAMA_BUILD_UI=OFF -DCMAKE_BUILD_TYPE=Release && cmake --build build --target llama-server -j 4
FROM nvidia/cuda:12.8.1-runtime-ubuntu22.04
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 libssl3 ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/build/bin/ /opt/llama/
ENV LD_LIBRARY_PATH=/opt/llama
ENTRYPOINT ["/opt/llama/llama-server"]
