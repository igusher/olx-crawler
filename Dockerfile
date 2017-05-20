FROM postgres:9.6
RUN mkdir -p /opt

RUN apt-get update
RUN apt-get -y install python-pip
RUN pip install --upgrade pip
RUN pip install --upgrade requests
RUN pip install --upgrade sqlalchemy
RUN pip install --upgrade psycopg2

ADD main.py /opt/main.py
ADD mymails.py /opt/mymails.py
RUN chmod +x /opt/main.py
ADD entrypoint.sh /opt/entrypoint.sh

ENTRYPOINT /opt/entrypoint.sh
