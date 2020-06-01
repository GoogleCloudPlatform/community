# Automatically generated build file. Do not edit.
COMPONENT_INCLUDES += $(IDF_PATH)/components/wpa_supplicant/include $(IDF_PATH)/components/wpa_supplicant/port/include $(IDF_PATH)/components/wpa_supplicant/include/esp_supplicant
COMPONENT_LDFLAGS += -L$(BUILD_DIR_BASE)/wpa_supplicant -lwpa_supplicant
COMPONENT_LINKER_DEPS += 
COMPONENT_SUBMODULES += 
COMPONENT_LIBRARIES += wpa_supplicant
COMPONENT_LDFRAGMENTS += 
component-wpa_supplicant-build: 
