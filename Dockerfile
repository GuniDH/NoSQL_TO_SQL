FROM python:3.10-slim

WORKDIR /app

# Copy the project files
COPY pyproject.toml poetry.lock* /app/
COPY json2csv/ /app/json2csv/
COPY sample_data/ /app/sample_data/

# Install Poetry
RUN pip install --no-cache-dir poetry

# Configure Poetry to not create a virtual environment in the container
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev

# Set the entrypoint to the json2csv command
ENTRYPOINT ["python", "-m", "json2csv.cli"]