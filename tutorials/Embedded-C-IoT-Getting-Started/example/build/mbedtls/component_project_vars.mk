# Automatically generated build file. Do not edit.
COMPONENT_INCLUDES += $(IDF_PATH)/components/mbedtls/port/include $(IDF_PATH)/components/mbedtls/mbedtls/include
COMPONENT_LDFLAGS += -L$(BUILD_DIR_BASE)/mbedtls -lmbedtls
COMPONENT_LINKER_DEPS += 
COMPONENT_SUBMODULES += $(IDF_PATH)/components/mbedtls/mbedtls
COMPONENT_LIBRARIES += mbedtls
COMPONENT_LDFRAGMENTS += 
component-mbedtls-build: 
