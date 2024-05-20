FROM python:3.11

ENV DEBIAN_FRONTEND noninteractive
ENV TERM linux

# Install dependencies for pyodbc.
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install --yes unixodbc-dev msodbcsql17

# Copy sources
COPY . /src

# Install package
RUN --mount=type=cache,id=pip,target=/root/.cache/pip \
    pip install --use-pep517 --prefer-binary '/src'

# Designate default program to invoke
CMD ["tsperf"]

# Purge /src and /tmp directories.
RUN rm -rf /src /tmp/*

# Copy selftest.sh to the image
COPY release/oci/selftest.sh /usr/local/bin
