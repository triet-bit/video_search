# syntax=docker/dockerfile:1
FROM docker.elastic.co/elasticsearch/elasticsearch:8.7.0
RUN bin/elasticsearch-plugin install --batch https://github.com/duydo/elasticsearch-analysis-vietnamese/releases/download/v8.7.0/elasticsearch-analysis-vietnamese-8.7.0.zip