cmake_minimum_required(VERSION 3.1)

project(smile)

set(CMAKE_C_FLAGS_DEBUG       "${CMAKE_C_FLAGG_DEBUG} -g -DDEBUG=1")
set(CMAKE_CXX_FLAGS_DEBUG     "${CMAKE_CXX_FLAGG_DEBUG} -g -DDEBUG=1")

set(SOURCE_FILES
    src/libsmile/lib/block.c
    src/libsmile/lib/decode.c)

include_directories(src/libsmile/include)

add_library(smile STATIC ${SOURCE_FILES} src/libsmile/lib/encode.h src/libsmile/lib/encode.c)


project(pysmile)

set(CMAKE_C_FLAGS_DEBUG       "${CMAKE_C_FLAGG_DEBUG} -g -DDEBUG=1")
set(CMAKE_CXX_FLAGS_DEBUG     "${CMAKE_CXX_FLAGG_DEBUG} -g -DDEBUG=1")

set(CMAKE_C_FLAGS             "${CMAKE_C_FLAGS} -std=c99 -dynamic -Wall -Wstrict-prototypes -pedantic -fomit-frame-pointer -Wno-tautological-compare -fno-common -fwrapv -pipe")
set(CMAKE_CXX_FLAGS           "${CMAKE_CXX_FLAGS} -std=c++11")

set(CMAKE_MODULE_LINKER_FLAGS "-Wl,-headerpad_max_install_names")

set(LIB_FILES
    smile
    python2.7)

set(SOURCE_FILES
    src/pysmile.c)

include_directories(/opt/local/Library/Frameworks/Python.framework/Versions/2.7/include/python2.7 src/libsmile/include)

add_library(pysmile MODULE ${SOURCE_FILES})
target_link_libraries(pysmile ${LIB_FILES})
set_target_properties(pysmile PROPERTIES PREFIX "")



project(unsmile)

set(SOURCE_FILES
    src/libsmile/tools/usage.c
    src/libsmile/tools/unsmile.c)

include_directories(src/libsmile/tools)
add_executable(unsmile ${SOURCE_FILES})
target_link_libraries(unsmile smile)

#enable_testing()
#add_test(NAME json-org-sample1 COMMAND test/test.sh)
# ${CMAKE_SOURCE_DIR}/test/data/json-org-sample1.smile