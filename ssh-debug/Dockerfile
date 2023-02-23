FROM debian:11.5-slim
MAINTAINER Eden Attenborough "gae19jtu@uea.ac.uk"

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get update -y
RUN apt-get install -y iputils-ping ssh rtklib

ENTRYPOINT ["ssh"]
