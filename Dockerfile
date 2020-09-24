FROM python:3

ADD src/data_generator/data_generator.py requirements.txt /app/src/data_generator/
ADD src/modules /app/src/modules/
ENV PYTHONPATH "${PYTHONPATH}:/app/src"
WORKDIR /app/src/data_generator
RUN pip install --upgrade pip && \
    pip install -r requirements.txt
CMD ["python", "./data_generator.py"]