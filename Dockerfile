# Use official Python image as base
FROM python:3.11.11-alpine

# Install system dependencies for MySQL/MariaDB connector
RUN apk add --no-cache mariadb-connector-c-dev gcc musl-dev

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY /code/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY /code .

# Expose the port Uvicorn will run on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
 