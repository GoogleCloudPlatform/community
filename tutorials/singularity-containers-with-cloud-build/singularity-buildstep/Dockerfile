FROM gcr.io/cloud-builders/go:debian

ARG singularity_version=3.0.2

RUN GOPATH=/go && \
    apt-get update && \
    apt-get install -y build-essential libssl-dev uuid-dev libgpgme11-dev squashfs-tools libseccomp-dev pkg-config && \
    go get -u github.com/golang/dep/cmd/dep && \
    mkdir -p ${GOPATH}/src/github.com/sylabs && \
    cd ${GOPATH}/src/github.com/sylabs && \
    git clone https://github.com/sylabs/singularity && \
    cd singularity && \
    git checkout v${singularity_version} && \
    ./mconfig && \
    cd builddir && \
    make install

ENTRYPOINT ["/usr/local/bin/singularity"]
