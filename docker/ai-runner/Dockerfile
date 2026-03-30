FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    bash \
    bubblewrap \
    ca-certificates \
    curl \
    git \
    jq \
    make \
    openssh-client \
    python3 \
    python3-pip \
    rsync \
    socat \
    unzip \
    vim \
    yq \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 -s /bin/bash dev && mkdir -p /workspace /state/home /state/cache /state/logs /run/secrets && chown -R dev:dev /workspace /state /run/secrets

COPY docker/ai-runner/entrypoint.sh /usr/local/bin/0dai-entrypoint
COPY docker/ai-runner/check-tools.sh /usr/local/bin/0dai-check-tools
COPY docker/ai-runner/examples/ /opt/0dai/examples/
RUN chmod +x /usr/local/bin/0dai-entrypoint /usr/local/bin/0dai-check-tools

USER dev
WORKDIR /workspace

ENV HOME=/state/home \
    CODEX_HOME=/state/home/.codex \
    XDG_CONFIG_HOME=/state/home/.config

ENTRYPOINT ["/usr/local/bin/0dai-entrypoint"]
CMD ["bash"]
