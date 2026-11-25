cmake_minimum_required(VERSION 3.16)
project(Geant4UnityServer)

find_package(Geant4 REQUIRED)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(${Geant4_USE_FILE})

include_directories(${PROJECT_SOURCE_DIR}/include)

set(SOURCES
    src/ActionInitialization.cc
    src/DetectorConstruction.cc
    src/EventAction.cc
    src/PhysicsList.cc
    src/PrimaryGeneratorAction.cc
    src/RunAction.cc
    src/SteppingAction.cc
    src/main_server.cc
)

add_executable(Geant4Server ${SOURCES})

target_link_libraries(Geant4Server ${Geant4_LIBRARIES})