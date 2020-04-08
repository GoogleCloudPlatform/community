apt update -y
while [ $? -ne 0 ]; do
  sleep 5
  apt update -y
done
apt install -y build-essential libssl-dev uuid-dev libgpgme11-dev squashfs-tools libseccomp-dev pkg-config git
while [ $? -ne 0 ]; do
  sleep 5
  apt install -y build-essential libssl-dev uuid-dev libgpgme11-dev squashfs-tools libseccomp-dev pkg-config git
done
cd /usr/local
sudo wget https://dl.google.com/go/go1.11.4.linux-amd64.tar.gz
sudo tar zxf go1.11.4.linux-amd64.tar.gz
export PATH=/usr/local/go/bin:$PATH
cd
mkdir -p /go/{bin,pkg,src}
export PATH=$PATH:/go/bin
export GOPATH=/go
go get -u github.com/golang/dep/cmd/dep
mkdir -p /go/src/github.com/sylabs
cd /go/src/github.com/sylabs
wget https://github.com/sylabs/singularity/releases/download/v3.0.2/singularity-3.0.2.tar.gz && \
    tar -xzvf singularity-3.0.2.tar.gz && \
    cd singularity && \
    ./mconfig -p /usr/local && \
    make -C builddir && \
    make -C builddir install
