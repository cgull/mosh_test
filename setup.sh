apt-get install mosh
yes "yes" | cpan IO::Pty::Easy
ssh-keygen -t rsa -f ./private_test_key2 -q -N ""
cat private_test_key.pub >> ~/.ssh/authorized_keys 