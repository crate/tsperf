FROM python:3

ADD data_generator setup.py /app/src/data_generator/
ENV PYTHONPATH "${PYTHONPATH}:/app/src"
WORKDIR /app/src/data_generator

# install dependencies for pyodbc
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 && \
    apt-get install -y unixodbc-dev

RUN pip install --upgrade pip && \
    pip install -e .
CMD ["python", "./__main__.py"]
