# serverfiles-dockerfiles

## Debugging the raspberry pi

A docker image is provided to reverse the connection from the wireguard tunnel and SSH into the pi. To build it@

`sudo docker build -t mower/ssh-debug ./ssh-debug`

To SSH into the pi:

`sudo docker run -it --rm --network container:server-dockerfiles_wireguard_1 -v "$(pwd)/../mower.pem:/mower.pem:ro" mower/ssh-debug pi@10.13.13.3 -i mower.pem`

To say, try to ping the pi:

`sudo docker run -it --rm --network container:server-dockerfiles_wireguard_1 -v "$(pwd)/../mower.pem:/mower.pem:ro" --entrypoint ping mower/ssh-debug 10.13.13.3`

Where the pi's wireguard IP is 10.13.13.3 and you are in the same directory as the docker-compose.
