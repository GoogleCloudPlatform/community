#!/bin/bash
#

sudo apt-get update
sudo apt-get -y install gawk wget git-core diffstat unzip texinfo gcc-multilib \
     build-essential chrpath socat cpio python python3 python3-pip python3-pexpect \
     xz-utils debianutils iputils-ping libsdl1.2-dev xterm
[ -d poky ] || git clone -b rocko git://git.yoctoproject.org/poky
cd poky
[ -d meta-mender ] || git clone -b rocko git://github.com/mendersoftware/meta-mender
[ -d meta-openembedded ] || git clone -b rocko git://git.openembedded.org/meta-openembedded
[ -d meta-raspberrypi ] || git clone -b rocko https://github.com/agherzan/meta-raspberrypi
[ -d meta-java ] || git clone -b rocko git://git.yoctoproject.org/meta-java
[ -d meta-iot-cloud ] || git clone -b rocko https://github.com/intel-iot-devkit/meta-iot-cloud.git
[ -d meta-gcp-iot ] || git clone -b master https://github.com/GoogleCloudPlatform/community.git
source ./oe-init-build-env
if [ -d ~/downloads ] ; then
    rm -rf ./downloads
    ln -s ~/downloads .
fi
if [ -d ~/sstate-cache ]; then
    rm -rf ./sstate-cache
    ln -s ~/sstate-cache .
fi
bitbake-layers add-layer -F ../meta-mender/meta-mender-core
bitbake-layers add-layer -F ../meta-openembedded/meta-oe
bitbake-layers add-layer -F ../meta-openembedded/meta-python
bitbake-layers add-layer -F ../meta-openembedded/meta-multimedia
bitbake-layers add-layer -F ../meta-openembedded/meta-networking
bitbake-layers add-layer -F ../meta-java
bitbake-layers add-layer -F ../meta-raspberrypi
bitbake-layers add-layer -F ../meta-mender/meta-mender-raspberrypi
bitbake-layers add-layer -F ../meta-iot-cloud
bitbake-layers add-layer -F ../community/tutorials/cloud-iot-mender-ota/image/meta-gcp-iot
cat > conf/auto.conf <<- EOF
	MACHINE="raspberrypi3"
	
	# Switch to systemd - required for Mender
	DISTRO_FEATURES_append += " systemd"
	VIRTUAL-RUNTIME_init_manager = "systemd"
	DISTRO_FEATURES_BACKFILL_CONSIDERED = "sysvinit"
	VIRTUAL-RUNTIME_initscripts = ""
	
	# Configure Mender
	INHERIT += "mender-full"
	MENDER_ARTIFACT_NAME = "release-1"
	MENDER_SERVER_URL = "https://mender.gcpotademo.com"
	IMAGE_INSTALL_append = " kernel-image kernel-devicetree"
	IMAGE_FSTYPES_append += " sdimg.bmap"
	
	# RPI specific additions for Mender
	RPI_USE_U_BOOT_rpi = "1"
	MENDER_PARTITION_ALIGNMENT_KB_rpi = "4096"
	MENDER_BOOT_PART_SIZE_MB_rpi = "40"
	MENDER_STORAGE_TOTAL_SIZE_MB_rpi = "2500"
	MENDER_DATA_PART_SIZE_MB_rpi = "500"
	IMAGE_FSTYPES_remove_rpi += " rpi-sdimg ext3"
	SDIMG_ROOTFS_TYPE_rpi = "ext4"
	ENABLE_UART_rpi = "1"
	
	PACKAGE_CLASSES = "package_ipk"
	INHERIT += "rm_work"
EOF
export FULL_PROJECT=$(gcloud config list project --format "value(core.project)")
export PROJECT_ID="$(echo $FULL_PROJECT | cut -f2 -d ':')"
export REGION_ID='us-central1'
export REGISTRY_ID='mender-demo'
export IMAGE='gcp-mender-demo-image'
export MACHINE='raspberrypi3'

# Ensure that the GCP variables defined above are passed into the bitbake environment
export BB_ENV_EXTRAWHITE="$BB_ENV_EXTRAWHITE PROJECT_ID REGION_ID REGISTRY_ID"

bitbake ${IMAGE}
cp ./tmp/deploy/images/${MACHINE}/${IMAGE}-${MACHINE}-*.sdimg ./tmp/deploy/images/${MACHINE}/${IMAGE}-${MACHINE}-*.img
gsutil cp $(find ./tmp/deploy/images/${MACHINE}/${IMAGE}-${MACHINE}-*.sdimg -type f) gs://$PROJECT_ID-mender-builds/${IMAGE}-${MACHINE}.sdimg
gsutil cp $(find ./tmp/deploy/images/${MACHINE}/${IMAGE}-${MACHINE}-*.sdimg.bmap -type f) gs://$PROJECT_ID-mender-builds/${IMAGE}-${MACHINE}.sdimg.bmap
gsutil cp $(find ./tmp/deploy/images/${MACHINE}/${IMAGE}-${MACHINE}-*.img -type f) gs://$PROJECT_ID-mender-builds/${IMAGE}-${MACHINE}.img
cat >> conf/auto.conf <<-	EOF
	MENDER_ARTIFACT_NAME = "release-2"
	IMAGE_INSTALL_append = " python-docs-samples"
EOF
bitbake ${IMAGE}
gsutil cp $(find ./tmp/deploy/images/${MACHINE}/${IMAGE}-${MACHINE}-*.mender -type f) gs://$PROJECT_ID-mender-builds/${IMAGE}-${MACHINE}.mender
