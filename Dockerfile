FROM python:3.11

ADD . /src

# Install dependencies for pyodbc.
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install --yes unixodbc-dev msodbcsql17

RUN pip install --upgrade pip && \
    pip install /src

CMD ["tsperf"]
