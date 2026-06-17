FROM python:3.9-slim

WORKDIR /code

# Copy requirements and install dependencies
COPY ./backend/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy backend files and data
COPY ./backend /code/backend
COPY ./data /code/data
COPY ./models /code/models

ENV PYTHONPATH=/code

EXPOSE 7860

# Run Gunicorn binding to port 7860
CMD ["gunicorn", "-b", "0.0.0.0:7860", "backend.main:app"]