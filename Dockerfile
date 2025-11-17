# Use Python 3.11 as the base image
FROM python:3.11-alpine

# Set working directory in container
WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml ./

# Install uv
RUN pip install uv

# Install dependencies using uv
RUN uv pip install --system flask flask-cors requests python-dotenv gunicorn

# Copy the rest of the application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose port 5000 for the Flask app
EXPOSE 5000

# Run the Flask app using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
