# Use a Python 3.8 base image
FROM python:3.8

# Set the working directory inside the container
WORKDIR /app


# Copy the current directory contents into the container at /app
COPY . /app

# Install virtualenv
RUN pip install virtualenv

# Create a virtual environment
RUN virtualenv venv

# Install Python dependencies and run setup.sh inside the virtual environment
RUN bash -c "source venv/bin/activate && \
    chmod +x /app/setup.sh && \
    ./setup.sh"

# Set the working directory
WORKDIR /app

# Expose port 5041 to allow external connections
EXPOSE 5041

# Command to run the application using the virtual environment's Python
CMD ["bash", "-c", "source venv/bin/activate && python run_app.py"]