FROM python:3.8


# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

# Make the main app folder
RUN mkdir -p /usr/src/app

# Set working dir
WORKDIR /usr/src/app

# Install packages 
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy all the app files to 
ADD . .

EXPOSE 80 5000

ENTRYPOINT ["python", "./app.py" ]
