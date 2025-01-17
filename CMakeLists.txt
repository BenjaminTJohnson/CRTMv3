#
# CRTM
# Copyright and License: see LICENSE

cmake_minimum_required( VERSION 3.12 )
project( crtm VERSION 3.0.0 LANGUAGES Fortran )

option(OPENMP "Build crtm with OpenMP support" ON)

## Ecbuild integration
find_package( ecbuild QUIET )
include( ecbuild_system NO_POLICY_SCOPE )
ecbuild_declare_project()
list( APPEND CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/cmake )
set( CMAKE_DIRECTORY_LABELS ${PROJECT_NAME} )

## Configuration options
include( ${PROJECT_NAME}_compiler_flags )
include(GNUInstallDirs)

## Dependencies
find_package( jedicmake QUIET )
if(OPENMP)
  find_package( OpenMP COMPONENTS Fortran )
endif()
find_package( NetCDF REQUIRED COMPONENTS Fortran )

## Sources
add_subdirectory( src )
add_subdirectory( test )
include(CTest)

ecbuild_install_project( NAME ${PROJECT_NAME} )
ecbuild_print_summary()
