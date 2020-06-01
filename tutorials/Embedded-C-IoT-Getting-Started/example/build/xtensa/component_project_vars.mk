# Automatically generated build file. Do not edit.
COMPONENT_INCLUDES += $(IDF_PATH)/components/xtensa/include $(IDF_PATH)/components/xtensa/esp32/include
COMPONENT_LDFLAGS += -L$(BUILD_DIR_BASE)/xtensa -lxtensa $(IDF_PATH)/components/xtensa/esp32/libhal.a
COMPONENT_LINKER_DEPS += 
COMPONENT_SUBMODULES += 
COMPONENT_LIBRARIES += xtensa
COMPONENT_LDFRAGMENTS += $(IDF_PATH)/components/xtensa/linker.lf
component-xtensa-build: 
