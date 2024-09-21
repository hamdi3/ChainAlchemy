# Use an official Python runtime as a parent image
FROM python:3.12.3-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file to the container
COPY requirements.txt /app/

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir pytest pytest-cov

# Add the src directory to the PYTHONPATH
ENV PYTHONPATH=/app/src

# Copy the entire Flask app code to the container
COPY . /app

# Set environment variables to make Flask work inside Docker
ENV FLASK_APP=src/main.py
ENV FLASK_RUN_HOST=0.0.0.0

# Expose port 5000 (Flask default port)
EXPOSE 5000

# Command to run the Flask app
CMD ["flask", "run"]
