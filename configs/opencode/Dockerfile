FROM python:3.12-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254
RUN apt-get update && apt-get install -y --no-install-recommends git bash ca-certificates \
    && rm -rf /var/lib/apt/lists/*
ENV XDG_CONFIG_HOME=/state/config XDG_DATA_HOME=/state/data \
    XDG_CACHE_HOME=/state/cache XDG_STATE_HOME=/state/state
WORKDIR /workspace
ENTRYPOINT ["/tools/opencode"]
