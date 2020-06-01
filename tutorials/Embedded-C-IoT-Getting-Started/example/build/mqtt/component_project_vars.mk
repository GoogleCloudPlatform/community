# Automatically generated build file. Do not edit.
COMPONENT_INCLUDES += $(IDF_PATH)/components/mqtt/esp-mqtt/include
COMPONENT_LDFLAGS += -L$(BUILD_DIR_BASE)/mqtt -lmqtt
COMPONENT_LINKER_DEPS += 
COMPONENT_SUBMODULES += $(IDF_PATH)/components/mqtt/esp-mqtt
COMPONENT_LIBRARIES += mqtt
COMPONENT_LDFRAGMENTS += 
component-mqtt-build: 
