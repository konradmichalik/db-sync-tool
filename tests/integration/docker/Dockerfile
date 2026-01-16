FROM python:3.11-slim

#
# Install required packages (minimal for db-sync-tool testing)
#
RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    curl \
    git \
    mariadb-client \
    netcat-openbsd \
    openssh-server \
    rsync \
    sshpass \
    php-cli \
 && rm -rf /var/lib/apt/lists/*

#
# Python dependencies
#
RUN pip3 install --no-cache-dir \
    paramiko>=4.0 \
    pyyaml>=6.0.2 \
    jsonschema>=4.20 \
    requests>=2.31.0 \
    semantic_version>=2.10.0 \
    rich>=13.0

#
# MariaDB client configuration (disable SSL for testing)
#
COPY my.cnf /etc/mysql/conf.d/

#
# SSH server setup
# https://forums.docker.com/t/ssh-from-one-containe-to-another-container/65906/9
#
RUN mkdir -p /var/run/sshd && \
    chmod 0755 /var/run/sshd && \
    useradd -p $(openssl passwd -1 password) --create-home --shell /bin/bash --groups sudo user

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
