FROM ros:humble-ros-base-jammy
MAINTAINER Eden Attenborough "gae19jtu@uea.ac.uk"

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get update -y
RUN apt-get install -y iputils-ping ros-humble-demo-nodes-cpp tmux python3-pip

COPY . /mower
WORKDIR /mower

RUN pip3 install -r requirements.txt

RUN git clone --recurse-submodules https://github.com/UEA-MComp/telemetry.git && cd telemetry && rosdep install -i --from-path src --rosdistro humble -y && colcon build --packages-select telemetry

RUN touch .docker

ENTRYPOINT ["bash"]
CMD ["entrypoint.sh"]

