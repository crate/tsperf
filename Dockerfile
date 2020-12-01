FROM python:3

ADD src/data_generator/data_generator.py requirements.txt /app/src/data_generator/
ADD src/modules /app/src/modules/
ENV PYTHONPATH "${PYTHONPATH}:/app/src"
WORKDIR /app/src/data_generator

# install dependencies for pyodbc
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 && \
    apt-get install -y unixodbc-dev

RUN pip install --upgrade pip && \
    pip install -r requirements.txt
CMD ["python", "./data_generator.py"]
