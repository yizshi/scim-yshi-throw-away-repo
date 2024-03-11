FROM python:3.11.7

# package setup
ADD requirements.txt  ./requirements.txt
RUN pip install -r requirements.txt

# environment setup
EXPOSE 13289
ADD . /app
WORKDIR /app

# app setup
ADD run.sh ./run.sh
CMD ./run.sh
