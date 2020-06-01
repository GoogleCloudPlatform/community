# Automatically generated build file. Do not edit.
COMPONENT_INCLUDES += $(IDF_PATH)/components/esp_rom/include
COMPONENT_LDFLAGS += -L$(BUILD_DIR_BASE)/esp_rom -lesp_rom -L $(IDF_PATH)/components/esp_rom/esp32/ld -T esp32.rom.ld -T esp32.rom.libgcc.ld -T esp32.rom.syscalls.ld -T esp32.rom.newlib-data.ld -T esp32.rom.newlib-funcs.ld 
COMPONENT_LINKER_DEPS += $(IDF_PATH)/components/esp_rom/esp32/ld/esp32.rom.ld $(IDF_PATH)/components/esp_rom/esp32/ld/esp32.rom.libgcc.ld $(IDF_PATH)/components/esp_rom/esp32/ld/esp32.rom.syscalls.ld $(IDF_PATH)/components/esp_rom/esp32/ld/esp32.rom.newlib-data.ld $(IDF_PATH)/components/esp_rom/esp32/ld/esp32.rom.newlib-funcs.ld
COMPONENT_SUBMODULES += 
COMPONENT_LIBRARIES += esp_rom
COMPONENT_LDFRAGMENTS += 
component-esp_rom-build: 
