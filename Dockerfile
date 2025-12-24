FROM python:3.11-slim

WORKDIR /usr/src/app

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire uc_intg_skyq package
COPY uc_intg_skyq/ ./uc_intg_skyq/
COPY driver.json ./

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV UC_CONFIG_HOME=/config

# Create config directory
RUN mkdir -p /config

# Expose port
EXPOSE 9090

# Run the integration using module entry point
CMD ["python", "-m", "uc_intg_skyq"]