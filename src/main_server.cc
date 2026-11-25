#include "DetectorConstruction.hh"
#include "PhysicsList.hh"
#include "ActionInitialization.hh"
#include "EventAction.hh"

#include <G4RunManager.hh>
#include <G4UImanager.hh>

#include <iostream>
#include <vector>
#include <cstring>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>

#define PORT 5000

struct StepData {
    float x, y, z;
    float px, py, pz;
    float energy;
};

G4RunManager* runManager = nullptr;

void SetupGeant4() {
    runManager = new G4RunManager();
    runManager->SetUserInitialization(new DetectorConstruction());
    runManager->SetUserInitialization(new PhysicsList());
    runManager->SetUserInitialization(new ActionInitialization());
    runManager->Initialize();
    
    G4UImanager* UI = G4UImanager::GetUIpointer();
    UI->ApplyCommand("/process/em/verbose 0");
    UI->ApplyCommand("/run/verbose 0");
    UI->ApplyCommand("/tracking/verbose 0");
}

int main() {
    std::cout << "[GEANT-SERVER] Starting Geant4 Initialization..." << std::endl;
    SetupGeant4();
    std::cout << "[GEANT-SERVER] Ready. Creating TCP Socket..." << std::endl;

    int server_fd, new_socket;
    struct sockaddr_in address;
    int opt = 1;
    int addrlen = sizeof(address);

    if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) == 0) {
        perror("socket failed");
        exit(EXIT_FAILURE);
    }

    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR | SO_REUSEPORT, &opt, sizeof(opt))) {
        perror("setsockopt");
        exit(EXIT_FAILURE);
    }

    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(PORT);

    if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) < 0) {
        perror("bind failed");
        exit(EXIT_FAILURE);
    }

    if (listen(server_fd, 3) < 0) {
        perror("listen");
        exit(EXIT_FAILURE);
    }

    std::cout << "[GEANT-SERVER] Listening on port " << PORT << "..." << std::endl;

    while(true) {
        std::cout << "[GEANT-SERVER] Waiting for Unity connection..." << std::endl;
        if ((new_socket = accept(server_fd, (struct sockaddr *)&address, (socklen_t*)&addrlen)) < 0) {
            perror("accept");
            continue;
        }
        std::cout << "[GEANT-SERVER] Unity Connected!" << std::endl;

        char buffer[1024] = {0};
        while(true) {
            int valread = read(new_socket, buffer, 1024);
            if (valread <= 0) {
                std::cout << "[GEANT-SERVER] Client disconnected." << std::endl;
                close(new_socket);
                break;
            }

            auto eventAction = const_cast<EventAction*>(static_cast<const EventAction*>(runManager->GetUserEventAction()));
            
            runManager->BeamOn(1);

            const std::vector<StepRecord>& records = eventAction->GetStepRecords();
            int count = records.size();

            send(new_socket, &count, sizeof(int), 0);

            if (count > 0) {
                std::vector<StepData> dataToSend;
                dataToSend.reserve(count);

                for(const auto& r : records) {
                    StepData sd;
                    sd.x = (float)(r.position.x() / CLHEP::cm);
                    sd.y = (float)(r.position.y() / CLHEP::cm);
                    sd.z = (float)(r.position.z() / CLHEP::cm);
                    sd.px = (float)(r.momentum.x() / CLHEP::MeV);
                    sd.py = (float)(r.momentum.y() / CLHEP::MeV);
                    sd.pz = (float)(r.momentum.z() / CLHEP::MeV);
                    sd.energy = (float)(r.kineticEnergy / CLHEP::MeV);
                    dataToSend.push_back(sd);
                }

                send(new_socket, dataToSend.data(), count * sizeof(StepData), 0);
            }
        }
    }

    delete runManager;
    return 0;
}