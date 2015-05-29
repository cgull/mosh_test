apt-get update
apt-get install mosh
sudo cpan IO::Pty::Easy
ssh-keygen -t rsa -f ./private_test_key -q -N ""
cat private_test_key.pub >> ~/.ssh/authorized_keys 
