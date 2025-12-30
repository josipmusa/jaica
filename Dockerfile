# Use official Python image
FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y --no-install-recommends build-essential
RUN apt-get install -y curl
RUN rm -rf /var/lib/apt/lists/*

# Copy dependency files first (for caching)
COPY requirements.txt ./

# Install pip dependencies
RUN pip install --upgrade pip
# Install torch first
RUN pip install --no-cache-dir torch==2.3.0+cu118 --index-url https://download.pytorch.org/whl/cu118
# Then install the rest of requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Copy the rest of the source code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run the FastAPI app
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
