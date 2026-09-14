FROM python:3-slim 
WORKDIR /usr/src/app/
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt 
COPY src/* ./
COPY instance/* ./instance/
VOLUME /usr/src/app/instance
CMD [ "python", "./review.py" ]