# Automatically generated build file. Do not edit.
COMPONENT_INCLUDES += $(IDF_PATH)/components/fatfs/diskio $(IDF_PATH)/components/fatfs/vfs $(IDF_PATH)/components/fatfs/src
COMPONENT_LDFLAGS += -L$(BUILD_DIR_BASE)/fatfs -lfatfs
COMPONENT_LINKER_DEPS += 
COMPONENT_SUBMODULES += 
COMPONENT_LIBRARIES += fatfs
COMPONENT_LDFRAGMENTS += 
component-fatfs-build: 
