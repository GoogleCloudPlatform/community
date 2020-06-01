# Automatically generated build file. Do not edit.
COMPONENT_INCLUDES += $(IDF_PATH)/components/esp_gdbstub/include
COMPONENT_LDFLAGS += -L$(BUILD_DIR_BASE)/esp_gdbstub -lesp_gdbstub
COMPONENT_LINKER_DEPS += 
COMPONENT_SUBMODULES += 
COMPONENT_LIBRARIES += esp_gdbstub
COMPONENT_LDFRAGMENTS += $(IDF_PATH)/components/esp_gdbstub/linker.lf
component-esp_gdbstub-build: 
