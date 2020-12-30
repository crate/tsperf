FROM python:3

# install dependencies for pyodbc
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 && \
    apt-get install -y unixodbc-dev

RUN pip install --upgrade pip && \
    pip install tsdb-data-generator
CMD ["tsdg"]
