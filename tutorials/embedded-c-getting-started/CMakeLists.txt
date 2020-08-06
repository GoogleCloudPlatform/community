#
# Component Makefile
#

set (GOOGLE_IOT_SDK ${CMAKE_CURRENT_LIST_DIR}/iot-device-sdk-embedded-c)

set (COMPONENT_ADD_INCLUDEDIRS
        "${GOOGLE_IOT_SDK}/src/bsp"
        "${GOOGLE_IOT_SDK}/include/bsp"
        "${GOOGLE_IOT_SDK}/include"
        "${GOOGLE_IOT_SDK}/src/libiotc/control_topic"
        "${GOOGLE_IOT_SDK}/src/libiotc/datastructures"
        "${GOOGLE_IOT_SDK}/src/libiotc/debug_extensions/memory_limiter"
        "${GOOGLE_IOT_SDK}/src/libiotc/event_dispatcher"
        "${GOOGLE_IOT_SDK}/src/libiotc/event_loop"
        "${GOOGLE_IOT_SDK}/src/libiotc/io/fs/memory"
        "${GOOGLE_IOT_SDK}/src/libiotc/io/fs"
        "${GOOGLE_IOT_SDK}/src/libiotc/io/net"
        "${GOOGLE_IOT_SDK}/src/libiotc/mqtt/logic"
        "${GOOGLE_IOT_SDK}/src/libiotc/mqtt/codec"
        "${GOOGLE_IOT_SDK}/src/libiotc/platform/iotc_thread"
        "${GOOGLE_IOT_SDK}/src/libiotc/platform/posix/iotc_thread"
        "${GOOGLE_IOT_SDK}/src/libiotc/tls"
        "${GOOGLE_IOT_SDK}/src/libiotc/tls/certs"
        "${GOOGLE_IOT_SDK}/src/libiotc/memory"
        "${GOOGLE_IOT_SDK}/src/libiotc"
        "${GOOGLE_IOT_SDK}/third_party/mqtt-protocol-c"
        "${GOOGLE_IOT_SDK}/../port/include")

set (COMPONENT_SRCDIRS
        "${GOOGLE_IOT_SDK}/src/bsp/tls/mbedtls"
        "${GOOGLE_IOT_SDK}/src/bsp/crypto/mbedtls"
        "${GOOGLE_IOT_SDK}/src/libiotc"
        "${GOOGLE_IOT_SDK}/src/libiotc/control_topic"
        "${GOOGLE_IOT_SDK}/src/libiotc/datastructures"
        "${GOOGLE_IOT_SDK}/src/libiotc/debug_extensions/memory_limiter"
        "${GOOGLE_IOT_SDK}/src/libiotc/event_dispatcher"
        "${GOOGLE_IOT_SDK}/src/libiotc/event_loop"
        "${GOOGLE_IOT_SDK}/src/libiotc/io/fs/memory"
        "${GOOGLE_IOT_SDK}/src/libiotc/io/fs"
        "${GOOGLE_IOT_SDK}/src/libiotc/io/net"
        "${GOOGLE_IOT_SDK}/src/libiotc/memory"
        "${GOOGLE_IOT_SDK}/src/libiotc/mqtt/codec"
        "${GOOGLE_IOT_SDK}/src/libiotc/mqtt/logic"
        "${GOOGLE_IOT_SDK}/src/libiotc/tls"
        "${GOOGLE_IOT_SDK}/src/libiotc/tls/certs"
        "${GOOGLE_IOT_SDK}/third_party/mqtt-protocol-c"
        "${GOOGLE_IOT_SDK}/../port/src")
        
set (COMPONENT_SUBMODULES "${GOOGLE_IOT_SDK}")

set (COMPONENT_OBJEXCLUDE "${GOOGLE_IOT_SDK}/src/libiotc/iotc_test.o")

set(COMPONENT_REQUIRES "mbedtls")

register_component()

target_compile_definitions(${COMPONENT_TARGET} PUBLIC
    -DIOTC_TLS_LIB_MBEDTLS
    -DIOTC_FS_MEMORY
    -DIOTC_MEMORY_LIMITER_APPLICATION_MEMORY_LIMIT=524288
    -DIOTC_MEMORY_LIMITER_SYSTEM_MEMORY_LIMIT=2024
    -DIOTC_MEMORY_LIMITER_ENABLED
)
