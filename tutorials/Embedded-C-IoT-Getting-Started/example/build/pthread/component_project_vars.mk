# Automatically generated build file. Do not edit.
COMPONENT_INCLUDES += $(IDF_PATH)/components/pthread/include
COMPONENT_LDFLAGS += -L$(BUILD_DIR_BASE)/pthread -lpthread -u pthread_include_pthread_impl -u pthread_include_pthread_cond_impl -u pthread_include_pthread_local_storage_impl
COMPONENT_LINKER_DEPS += 
COMPONENT_SUBMODULES += 
COMPONENT_LIBRARIES += pthread
COMPONENT_LDFRAGMENTS += 
component-pthread-build: 
