# Automatically generated build file. Do not edit.
COMPONENT_INCLUDES += $(IDF_PATH)/components/asio/asio/asio/include $(IDF_PATH)/components/asio/port/include
COMPONENT_LDFLAGS += -L$(BUILD_DIR_BASE)/asio -lasio
COMPONENT_LINKER_DEPS += 
COMPONENT_SUBMODULES += $(IDF_PATH)/components/asio/asio
COMPONENT_LIBRARIES += asio
COMPONENT_LDFRAGMENTS += 
component-asio-build: 
