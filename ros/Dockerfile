FROM ros:humble-ros-base-jammy
MAINTAINER Eden Attenborough "gae19jtu@uea.ac.uk"

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get update -y
RUN apt-get install -y iputils-ping

COPY . /mower
WORKDIR /mower

# placeholder stuff...
ENTRYPOINT ["ping"]
CMD ["10.13.13.3"]

