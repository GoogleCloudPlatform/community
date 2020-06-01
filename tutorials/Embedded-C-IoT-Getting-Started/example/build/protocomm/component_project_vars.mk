# Automatically generated build file. Do not edit.
COMPONENT_INCLUDES += $(IDF_PATH)/components/protocomm/include/common $(IDF_PATH)/components/protocomm/include/security $(IDF_PATH)/components/protocomm/include/transports
COMPONENT_LDFLAGS += -L$(BUILD_DIR_BASE)/protocomm -lprotocomm
COMPONENT_LINKER_DEPS += 
COMPONENT_SUBMODULES += 
COMPONENT_LIBRARIES += protocomm
COMPONENT_LDFRAGMENTS += 
component-protocomm-build: 
