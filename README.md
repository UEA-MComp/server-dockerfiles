# serverfiles-dockerfiles

This repository contains the code for the server-side part of the system. The server can be accessed at `mcomp@mower.awiki.org -p 2323`. If you need an SSH key, or to add your SSH key, message Eden.

## VPN notes

A VPN used to connect the raspberry pi to the server. This is done so that ROS nodes can communicate nicely. The same VPN connection can also be used to SSH into and debug the pi. To connect to the raspberry pi, you need to connect to the same VPN network that it is connected to (yes, even on this server (annoying I know)). A wireguard configuration to do this is provided, message Eden for it (`mower_conf.conf`), alternatively you can use the docker image which connects to the VPN for you (see [Debugging the raspberry pi](https://github.com/UEA-MComp/server-dockerfiles#debugging-the-raspberry-pi))

Originally the plan was to have a docker container for the VPN server, but instead the VPN server runs on my pfsense router. The docker image `wireguard` connects to this VPN, so therefore by sharing this docker containers network, you can connect containers to the VPN. This is what the ROS container, and the debugging container do.

![Public IP address leak uwu](https://i.imgur.com/oQ4O0XZ.png)

The raspberry pi's IP address on the VPN network is 10.13.13.3.

## Debugging the raspberry pi

A docker image is provided to reverse the connection from the wireguard tunnel and SSH into the pi. To (re)build it if you need to:

`sudo docker build -t mower/ssh-debug ./ssh-debug`

To SSH into the pi:

`sudo docker run -it --rm --network container:server-dockerfiles_wireguard_1 -v "$(pwd)/../mower.pem:/mower.pem:ro" mower/ssh-debug pi@10.13.13.3 -i mower.pem`

To say, try to ping the pi:

`sudo docker run -it --rm --network container:server-dockerfiles_wireguard_1 -v "$(pwd)/../mower.pem:/mower.pem:ro" --entrypoint ping mower/ssh-debug 10.13.13.3`

Where the pi's wireguard IP is 10.13.13.3 and you are in the same directory as the docker-compose.

## Notes

Getting the latest robot location:

`SELECT recv_at, x, y, z FROM telemetry INNER JOIN coords ON coords.coord_id = telemetry.coord ORDER BY recv_at DESC LIMIT 1;`

