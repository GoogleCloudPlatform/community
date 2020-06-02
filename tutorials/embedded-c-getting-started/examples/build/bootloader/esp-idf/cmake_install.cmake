# Install script for directory: /Users/galzahavi/esp-idf

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/usr/local")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Is this installation the result of a crosscompile?
if(NOT DEFINED CMAKE_CROSSCOMPILING)
  set(CMAKE_CROSSCOMPILING "TRUE")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for each subdirectory.
  include("/Users/galzahavi/Desktop/GCP/community/tutorials/embedded-c-getting-started/examples/build/bootloader/esp-idf/esp32/cmake_install.cmake")
  include("/Users/galzahavi/Desktop/GCP/community/tutorials/embedded-c-getting-started/examples/build/bootloader/esp-idf/soc/cmake_install.cmake")
  include("/Users/galzahavi/Desktop/GCP/community/tutorials/embedded-c-getting-started/examples/build/bootloader/esp-idf/xtensa/cmake_install.cmake")
  include("/Users/galzahavi/Desktop/GCP/community/tutorials/embedded-c-getting-started/examples/build/bootloader/esp-idf/esp_common/cmake_install.cmake")
  include("/Users/galzahavi/Desktop/GCP/community/tutorials/embedded-c-getting-started/examples/build/bootloader/esp-idf/esp_rom/cmake_install.cmake")
  include("/Users/galzahavi/Desktop/GCP/community/tutorials/embedded-c-getting-started/examples/build/bootloader/esp-idf/log/cmake_install.cmake")
  include("/Users/galzahavi/Desktop/GCP/community/tutorials/embedded-c-getting-started/examples/build/bootloader/esp-idf/partition_table/cmake_install.cmake")
  include("/Users/galzahavi/Desktop/GCP/community/tutorials/embedded-c-getting-started/examples/build/bootloader/esp-idf/bootloader/cmake_install.cmake")
  include("/Users/galzahavi/Desktop/GCP/community/tutorials/embedded-c-getting-started/examples/build/bootloader/esp-idf/micro-ecc/cmake_install.cmake")
  include("/Users/galzahavi/Desktop/GCP/community/tutorials/embedded-c-getting-started/examples/build/bootloader/esp-idf/spi_flash/cmake_install.cmake")
  include("/Users/galzahavi/Desktop/GCP/community/tutorials/embedded-c-getting-started/examples/build/bootloader/esp-idf/efuse/cmake_install.cmake")
  include("/Users/galzahavi/Desktop/GCP/community/tutorials/embedded-c-getting-started/examples/build/bootloader/esp-idf/bootloader_support/cmake_install.cmake")
  include("/Users/galzahavi/Desktop/GCP/community/tutorials/embedded-c-getting-started/examples/build/bootloader/esp-idf/esptool_py/cmake_install.cmake")
  include("/Users/galzahavi/Desktop/GCP/community/tutorials/embedded-c-getting-started/examples/build/bootloader/esp-idf/main/cmake_install.cmake")

endif()

