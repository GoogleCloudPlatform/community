#
# Component Makefile
#

COMPONENT_ADD_INCLUDEDIRS := \
        iot-device-sdk-embedded-c/src/bsp \
        iot-device-sdk-embedded-c/include/bsp \
        iot-device-sdk-embedded-c/include \
        iot-device-sdk-embedded-c/src/libiotc/control_topic \
        iot-device-sdk-embedded-c/src/libiotc/datastructures \
        iot-device-sdk-embedded-c/src/libiotc/debug_extensions/memory_limiter \
        iot-device-sdk-embedded-c/src/libiotc/event_dispatcher \
        iot-device-sdk-embedded-c/src/libiotc/event_loop \
        iot-device-sdk-embedded-c/src/libiotc/io/fs/memory \
        iot-device-sdk-embedded-c/src/libiotc/io/fs \
        iot-device-sdk-embedded-c/src/libiotc/io/net \
        iot-device-sdk-embedded-c/src/libiotc/mqtt/logic \
        iot-device-sdk-embedded-c/src/libiotc/mqtt/codec \
        iot-device-sdk-embedded-c/src/libiotc/platform/iotc_thread \
        iot-device-sdk-embedded-c/src/libiotc/platform/posix/iotc_thread \
        iot-device-sdk-embedded-c/src/libiotc/tls \
        iot-device-sdk-embedded-c/src/libiotc/tls/certs \
        iot-device-sdk-embedded-c/src/libiotc/memory \
        iot-device-sdk-embedded-c/src/libiotc \
        iot-device-sdk-embedded-c/third_party/mqtt-protocol-c \
        port/include



COMPONENT_SRCDIRS := \
        iot-device-sdk-embedded-c/src/bsp/tls/mbedtls \
        iot-device-sdk-embedded-c/src/bsp/crypto/mbedtls \
        iot-device-sdk-embedded-c/src/libiotc \
        iot-device-sdk-embedded-c/src/libiotc/control_topic \
        iot-device-sdk-embedded-c/src/libiotc/datastructures \
        iot-device-sdk-embedded-c/src/libiotc/debug_extensions/memory_limiter \
        iot-device-sdk-embedded-c/src/libiotc/event_dispatcher \
        iot-device-sdk-embedded-c/src/libiotc/event_loop \
        iot-device-sdk-embedded-c/src/libiotc/io/fs \
        iot-device-sdk-embedded-c/src/libiotc/io/fs/memory \
        iot-device-sdk-embedded-c/src/libiotc/io/net \
        iot-device-sdk-embedded-c/src/libiotc/memory \
        iot-device-sdk-embedded-c/src/libiotc/mqtt/codec \
        iot-device-sdk-embedded-c/src/libiotc/mqtt/logic \
        iot-device-sdk-embedded-c/src/libiotc/mqtt/tls \
        iot-device-sdk-embedded-c/src/libiotc/tls \
        iot-device-sdk-embedded-c/src/libiotc/tls/certs \
        iot-device-sdk-embedded-c/third_party/mqtt-protocol-c \
        port/src

COMPONENT_SUBMODULES := iot-device-sdk-embedded-c

COMPONENT_OBJEXCLUDE := iot-device-sdk-embedded-c/src/libiotc/iotc_test.o \
                        iot-device-sdk-embedded-c/src/libiotc/iotc_jwt_test.o \
                        iot-device-sdk-embedded-c/src/libiotc/event_dispatcher/iotc_event_dispatcher_test.o \
                        iot-device-sdk-embedded-c/src/libiotc/event_dispatcher/iotc_event_handle_test.o

CFLAGS += -DIOTC_FS_MEMORY \
          -DIOTC_MEMORY_LIMITER_APPLICATION_MEMORY_LIMIT=524288 \
          -DIOTC_MEMORY_LIMITER_SYSTEM_MEMORY_LIMIT=2024 \
          -DIOTC_MEMORY_LIMITER_ENABLED \
          -DIOTC_TLS_LIB_MBEDTLS \

ifdef CONFIG_GIOT_DEBUG_OUTPUT
CFLAGS += -DIOTC_DEBUG_OUTPUT=1
endif
