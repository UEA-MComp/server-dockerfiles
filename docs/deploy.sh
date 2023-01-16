tar czvf build.tar.gz build/
scp build.tar.gz eden@docs.mower.awiki.org:/home/eden/MowerDocs/build.tar.gz
rm build.tar.gz
ssh eden@docs.mower.awiki.org "rm -rf /home/eden/MowerDocs/build/"
ssh eden@docs.mower.awiki.org "tar xvf /home/eden/MowerDocs/build.tar.gz -C /home/eden/MowerDocs"
ssh eden@docs.mower.awiki.org "rm /home/eden/MowerDocs/build.tar.gz"
ssh eden@docs.mower.awiki.org "chmod 755 -R /home/eden/MowerDocs/build/"