FROM gcr.io/cloud-builders/go:debian

ARG singularity_version=3.0.2

# See https://github.com/singularityhub/singularity-docker/blob/3.0.2/Dockerfile

RUN GOPATH=/go && \
    apt-get update && \
    apt-get install -y build-essential libssl-dev uuid-dev libgpgme11-dev squashfs-tools libseccomp-dev pkg-config wget && \
    go get -u github.com/golang/dep/cmd/dep && \
    mkdir -p ${GOPATH}/src/github.com/sylabs && \
    cd ${GOPATH}/src/github.com/sylabs && \
    wget https://github.com/sylabs/singularity/releases/download/v${singularity_version}/singularity-${singularity_version}.tar.gz && \
    tar -xzvf singularity-${singularity_version}.tar.gz && \
    cd singularity && \
    ./mconfig -p /usr/local && \
    make -C builddir && \
    make -C builddir install

ENTRYPOINT ["/usr/local/bin/singularity"]
