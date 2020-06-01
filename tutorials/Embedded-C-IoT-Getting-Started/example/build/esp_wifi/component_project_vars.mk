# Automatically generated build file. Do not edit.
COMPONENT_INCLUDES += $(IDF_PATH)/components/esp_wifi/include $(IDF_PATH)/components/esp_wifi/esp32/include
COMPONENT_LDFLAGS += -L$(BUILD_DIR_BASE)/esp_wifi -lesp_wifi -L$(IDF_PATH)/components/esp_wifi/lib_esp32 -lcore -lrtc -lnet80211 -lpp -lsmartconfig -lcoexist -lespnow -lphy -lmesh
COMPONENT_LINKER_DEPS += $(IDF_PATH)/components/esp_wifi/lib_esp32/libcore.a $(IDF_PATH)/components/esp_wifi/lib_esp32/librtc.a $(IDF_PATH)/components/esp_wifi/lib_esp32/libnet80211.a $(IDF_PATH)/components/esp_wifi/lib_esp32/libpp.a $(IDF_PATH)/components/esp_wifi/lib_esp32/libsmartconfig.a $(IDF_PATH)/components/esp_wifi/lib_esp32/libcoexist.a $(IDF_PATH)/components/esp_wifi/lib_esp32/libespnow.a $(IDF_PATH)/components/esp_wifi/lib_esp32/libphy.a $(IDF_PATH)/components/esp_wifi/lib_esp32/libmesh.a
COMPONENT_SUBMODULES += $(IDF_PATH)/components/esp_wifi/lib_esp32
COMPONENT_LIBRARIES += esp_wifi
COMPONENT_LDFRAGMENTS += $(IDF_PATH)/components/esp_wifi/linker.lf
component-esp_wifi-build: 
