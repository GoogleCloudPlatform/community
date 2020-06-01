# Automatically generated build file. Do not edit.
COMPONENT_INCLUDES += $(IDF_PATH)/components/expat/expat/expat/lib $(IDF_PATH)/components/expat/port/include
COMPONENT_LDFLAGS += -L$(BUILD_DIR_BASE)/expat -lexpat
COMPONENT_LINKER_DEPS += 
COMPONENT_SUBMODULES += $(IDF_PATH)/components/expat/expat
COMPONENT_LIBRARIES += expat
COMPONENT_LDFRAGMENTS += 
component-expat-build: 
