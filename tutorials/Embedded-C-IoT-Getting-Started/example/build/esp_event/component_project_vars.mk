# Automatically generated build file. Do not edit.
COMPONENT_INCLUDES += $(IDF_PATH)/components/esp_event/include
COMPONENT_LDFLAGS += -L$(BUILD_DIR_BASE)/esp_event -lesp_event
COMPONENT_LINKER_DEPS += 
COMPONENT_SUBMODULES += 
COMPONENT_LIBRARIES += esp_event
COMPONENT_LDFRAGMENTS += $(IDF_PATH)/components/esp_event/linker.lf
component-esp_event-build: 
