FROM python:3.12-alpine

# Set the working directory
WORKDIR /app

RUN pip install gunicorn

COPY requirements.txt .

# Install dependencies
# RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# ENV PORT=5000

EXPOSE 5000

# Run app.py when the container launches
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "django_commerce.wsgi:application"]