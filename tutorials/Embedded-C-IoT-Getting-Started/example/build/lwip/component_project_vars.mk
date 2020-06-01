# Automatically generated build file. Do not edit.
COMPONENT_INCLUDES += $(IDF_PATH)/components/lwip/include/apps $(IDF_PATH)/components/lwip/include/apps/sntp $(IDF_PATH)/components/lwip/lwip/src/include $(IDF_PATH)/components/lwip/port/esp32/include $(IDF_PATH)/components/lwip/port/esp32/include/arch
COMPONENT_LDFLAGS += -L$(BUILD_DIR_BASE)/lwip -llwip
COMPONENT_LINKER_DEPS += 
COMPONENT_SUBMODULES += $(IDF_PATH)/components/lwip/lwip
COMPONENT_LIBRARIES += lwip
COMPONENT_LDFRAGMENTS += $(IDF_PATH)/components/lwip/linker.lf
component-lwip-build: 
