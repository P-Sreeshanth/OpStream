# Base Image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install ast-grep
RUN curl -Ls https://github.com/ast-grep/ast-grep/releases/download/0.11.0/ast-grep-x86_64-unknown-linux-gnu.tar.gz | tar -xz -C /usr/local/bin

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the backend API
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
