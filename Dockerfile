FROM python:3

ADD dist/tsdb_data_generator-1.1.0-py3-none-any.whl /app/

# install dependencies for pyodbc
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 && \
    apt-get install -y unixodbc-dev

RUN pip install --upgrade pip && \
    pip install /app/tsdb_data_generator-1.1.0-py3-none-any.whl
CMD ["tsdg"]
