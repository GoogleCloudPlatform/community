# Automatically generated build file. Do not edit.
COMPONENT_INCLUDES += $(IDF_PATH)/components/heap/include
COMPONENT_LDFLAGS += -L$(BUILD_DIR_BASE)/heap -lheap
COMPONENT_LINKER_DEPS += 
COMPONENT_SUBMODULES += 
COMPONENT_LIBRARIES += heap
COMPONENT_LDFRAGMENTS += $(IDF_PATH)/components/heap/linker.lf
component-heap-build: 
