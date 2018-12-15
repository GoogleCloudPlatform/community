SUMMARY = "Mender Google IOT Activation Agent and Launch Script"
LICENSE = "Apache-2.0"

SRC_URI = " \
	file://${PN}.service \
	file://activate_agent.py \
	file://wait-for-timesync \
	file://LICENSE \
"
LIC_FILES_CHKSUM = "file://${WORKDIR}/LICENSE;md5=e3fc50a88d0a364313df4b21ef20c29e"

inherit systemd

SYSTEMD_SERVICE_${PN} = "${PN}.service"
FILES_${PN} += " \
    ${systemd_unitdir}/system/${PN}.service \
    /opt/gcp${bindir}/activate_agent.py \
    /opt/gcp${bindir}/wait-for-timesync \
"

do_install() {
  install -d ${D}${systemd_unitdir}/system
  install -m 0644 ${WORKDIR}/${PN}.service ${D}${systemd_unitdir}/system/
  install -d ${D}/opt/gcp${bindir}
  install -m 0755 ${WORKDIR}/activate_agent.py ${D}/opt/gcp${bindir}/
  install -m 0755 ${WORKDIR}/wait-for-timesync ${D}/opt/gcp${bindir}/
}

RDEPENDS_${PN} += "bash python gcp-config"
DEPENDS += "gcp-root-certs"
