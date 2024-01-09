cmake_minimum_required(VERSION 3.18 FATAL_ERROR)
option(WITH_PUBLISH "Publish on PyPi" OFF)
option(WITH_DOCS "Geenrating the documentation for the code" OFF)

project(qiskit_pqcee_provider
        VERSION 0.1.1
        DESCRIPTION "The pQCee blockhain qiskit provier"
        LANGUAGES NONE)

set(CMAKE_MODULE_PATH "${PROJECT_SOURCE_DIR}/cmake" ${CMAKE_MODULE_PATH})

if(WITH_DOCS)
        add_subdirectory("${PROJECT_SOURCE_DIR}/docs")
endif()
if(WITH_PUBLISH)
        add_subdirectory("${PROJECT_SOURCE_DIR}/qiskit_pqcee_provider")
endif()