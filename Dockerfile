# Use an official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose the port your app runs on (e.g., Uvicorn for FastAPI)
EXPOSE 8000

# Start the app (edit this as needed for your framework)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

