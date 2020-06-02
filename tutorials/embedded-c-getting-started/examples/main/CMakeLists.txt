set(COMPONENT_SRCS "getting-started.c")
set(COMPONENT_ADD_INCLUDEDIRS ".")

register_component()

if(IDF_CI_BUILD)
     add_custom_command(OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/certs/private_key.pem
                         COMMAND echo "Dummy certificate data for continuous integration" >
                                 certs/private_key.pem
                         WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
                         VERBATIM)
     add_custom_target(example_certificates DEPENDS ${CMAKE_CURRENT_BINARY_DIR}/certs/private_key.pem)

     add_dependencies(${COMPONENT_TARGET} example_certificates)

     target_add_binary_data(${COMPONENT_TARGET} "${CMAKE_CURRENT_BINARY_DIR}/certs/private_key.pem" TEXT)
 else()
    target_add_binary_data(${COMPONENT_TARGET} "certs/private_key.pem" TEXT)
 endif()

