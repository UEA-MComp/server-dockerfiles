source /opt/ros/humble/setup.bash
tmux new-session -d -s "fastdds" 'bash -ic "bash /mower/fastdds-tmux.sh" || bash && bash';

source /mower/LocationPublisher/install/setup.bash 
export ROS_DISCOVERY_SERVER=localhost:11811
export ROS2_DOMAIN_ID=142
ros2 run loc_updater loc_reciever
