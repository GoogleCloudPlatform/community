# Automatically generated build file. Do not edit.
COMPONENT_INCLUDES += $(IDF_PATH)/components/app_update/include
COMPONENT_LDFLAGS += -L$(BUILD_DIR_BASE)/app_update -lapp_update -u esp_app_desc
COMPONENT_LINKER_DEPS += 
COMPONENT_SUBMODULES += 
COMPONENT_LIBRARIES += app_update
COMPONENT_LDFRAGMENTS += 
component-app_update-build: 
