# Use the official Apache Airflow image as the base
FROM apache/airflow:2.7.1-python3.10

# Switch to the airflow user to install Python packages
USER airflow

# Copy our requirements file into the container
COPY requirements.txt /requirements.txt

# Install the packages
RUN pip install --no-cache-dir -r /requirements.txt