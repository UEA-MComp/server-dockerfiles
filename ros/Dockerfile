FROM ros:humble-ros-base-jammy
MAINTAINER Eden Attenborough "gae19jtu@uea.ac.uk"

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get update -y
RUN apt-get install -y iputils-ping ros-humble-demo-nodes-cpp tmux

COPY . /mower
WORKDIR /mower

ENTRYPOINT ["bash"]
CMD ["entrypoint.sh"]

