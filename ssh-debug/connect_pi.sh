sudo docker run -it --rm --network container:server-dockerfiles_wireguard_1 -v "$(pwd)/../../mower.pem:/mower.pem:ro" mower/ssh-debug pi@10.13.13.3 -i mower.pem
