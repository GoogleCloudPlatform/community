SUMMARY = "Google Cloud Platform Root Certificates"
LICENSE = "Apache-2.0"
LIC_FILES_CHKSUM = "file://LICENSE;md5=86d3f3a95c324c9479bd8986968f4327"

SRC_URI = " \
     git://github.com/GoogleCloudPlatform/python-docs-samples;branch=master \
"
SRCREV = "47a39ccedf3cfdaa7825269800af7bf1294cc79c"

S = "${WORKDIR}/git"
B = "${WORKDIR}/build"

inherit deploy

do_deploy() {
    install -d ${DEPLOYDIR}/persist/gcp
    install -m 0700 ${S}/iot/api-client/mqtt_example/resources/roots.pem ${DEPLOYDIR}/persist/gcp
}
addtask do_deploy after do_install before do_package
