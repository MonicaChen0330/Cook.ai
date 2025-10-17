# Use the official Python 3.10 slim image as a base
FROM python:3.10-slim

# Create a working directory in the container
WORKDIR /app

# Copy the dependency list
COPY requirements.txt .

# Install all dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your code
COPY . .

# Command to run when the container starts
CMD ["flask", "run", "--host=0.0.0.0"]
