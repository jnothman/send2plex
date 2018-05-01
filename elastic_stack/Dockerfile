ARG ES_VERSION=6.2.4
FROM docker.elastic.co/beats/filebeat:${ES_VERSION}
COPY filebeat.yml /usr/share/filebeat/filebeat.yml
USER root
RUN chown root /usr/share/filebeat/filebeat.yml