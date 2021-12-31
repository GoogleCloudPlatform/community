FILESEXTRAPATHS_prepend := "${THISDIR}/files:"

SRC_URI += " \
    file://gcp-iot-mender-device-identity \
    file://mender.conf \
    file://mender-generate-certificate \
"

FILES_${PN} += " \
     ${sbindir}/mender-keygen-client \
     ${sbindir}/mender-generate-certificate \
"

do_install_prepend() {
    # Update the service file to invoke mender-generate-certificate
    cat >> ${WORKDIR}/${SYSTEMD_SERVICE_${PN}} <<-EOF
	
	[Service]
	ExecStartPre=${sbindir}/mender-generate-certificate
	EOF
}

do_install_append() {
    install -d ${D}/${datadir}/mender/identity
    install -m 0755  ${WORKDIR}/gcp-iot-mender-device-identity ${D}/${datadir}/mender/identity/mender-device-identity
    install -d ${D}/${sbindir}
    install -m 0700 ${S}/src/${GO_IMPORT}/support/keygen-client ${D}/${sbindir}/mender-keygen-client
    install -m 0700 ${WORKDIR}/mender-generate-certificate ${D}/${sbindir}/
}

MENDER_UPDATE_POLL_INTERVAL_SECONDS = "30"
MENDER_INVENTORY_POLL_INTERVAL_SECONDS = "30"
MENDER_RETRY_POLL_INTERVAL_SECONDS = "30"

do_compile_prepend() {
  bbwarn "You are building with the meta-gcp-iot layer, which is not intended for production use"
}

RDEPENDS_${PN} += " bash openssl"

inherit deploy

do_deploy() {
   install -d ${DEPLOYDIR}/persist/mender
   mv ${D}${sysconfdir}/mender/mender.conf ${DEPLOYDIR}/persist/mender
   ln -s /data/mender/mender.conf ${D}${sysconfdir}/mender/mender.conf
}
addtask do_deploy after do_install before do_package
