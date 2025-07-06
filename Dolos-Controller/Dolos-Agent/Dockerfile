FROM ubuntu:20.04

# Set non-interactive frontend for apt
ENV DEBIAN_FRONTEND=noninteractive

# Đảm bảo user là root
USER root

# Cài đặt các gói cần thiết
RUN apt-get update && \
    apt-get install -y \
        software-properties-common \
        curl \
        wget \
        ca-certificates \
        build-essential \
        libffi-dev \
        libssl-dev \
        libpcap-dev \
        zlib1g-dev \
        pkg-config \
        rustc \
        python3-pip \
        python3-dev \
        python3-setuptools \
        iptables \
        sqlite3 \
        endlessh && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && \
    apt-get install -y \
        python3.7 \
        python3.7-dev \
        python3.7-distutils \
        python3.8 \
        python3.8-dev \
        python3.8-distutils \
        libpython3.8 && \
    rm -rf /var/lib/apt/lists/*

# Cài pip cho Python 3.7
RUN curl -sS https://bootstrap.pypa.io/pip/3.7/get-pip.py | python3.7

# Cài pip cho Python 3.8 (fix lỗi này)
RUN curl -sS https://bootstrap.pypa.io/pip/3.8/get-pip.py | python3.8

# Verify pip installation
RUN python3.7 -m pip --version && python3.8 -m pip --version

# Cài thư viện Python cho Python 3.7
RUN python3.7 -m pip install --no-cache-dir --upgrade pip && \
    python3.7 -m pip install --no-cache-dir scapy cryptography cffi pypcap dpkt

# Cài thư viện Python cho Python 3.8
RUN python3.8 -m pip install --no-cache-dir --upgrade pip && \
    python3.8 -m pip install --no-cache-dir scapy cryptography cffi pypcap dpkt

# Thêm vào Dockerfile
RUN mkdir -p /var/log && chmod 777 /var/log

# Tạo thư mục chứa mã nguồn
WORKDIR /opt/app

# Copy toàn bộ mã nguồn vào container
COPY . /opt/app

# Cấp quyền thực thi cho tất cả scripts
RUN find /opt/app -name "*.sh" -exec chmod +x {} \; && \
    find /opt/app -name "*.py" -exec chmod +x {} \;


# Lệnh mặc định khi container khởi động
CMD ["/bin/bash"]
