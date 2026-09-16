FROM python:3.11-slim
WORKDIR /usr/src/app/
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY src/* ./
CMD [ "python", "./cart.py" ]
