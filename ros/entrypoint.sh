tmux new-session -d -s "fastdds" 'bash -ic "bash /mower/fastdds-tmux.sh" || bash && bash';


. /opt/ros/humble/setup.bash
export ROS2_DOMAIN_ID=142
export ROS_DISCOVERY_SERVER=127.0.0.1:11811


# placeholder so it doesn't exit straight away
ping 10.13.13.3
