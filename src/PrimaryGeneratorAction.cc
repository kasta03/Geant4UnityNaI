#include "PrimaryGeneratorAction.hh"
#include <G4Event.hh>
#include <G4ParticleGun.hh>
#include <G4ParticleDefinition.hh>
#include <G4ParticleTable.hh>
#include <G4SystemOfUnits.hh>
#include <G4ThreeVector.hh>
#include <cstdlib>
#include <G4ios.hh>

PrimaryGeneratorAction::PrimaryGeneratorAction() {
    fParticleGun = new G4ParticleGun(1);
    float energyVal = std::getenv("PARTICLE_ENERGY") ? std::atof(std::getenv("PARTICLE_ENERGY")) : 10.0;
    const char *pName = std::getenv("PARTICLE_NAME") ? std::getenv("PARTICLE_NAME") : "e-";
    auto *particle = G4ParticleTable::GetParticleTable()->FindParticle(pName);
    if (particle)
    {
        fParticleGun->SetParticleDefinition(particle);
        G4cout << "[INFO] Particle " << pName << " found and set." << G4endl;
    }
    else
    {
        G4cout << "[ERROR] Particle " << pName << " not found! Using electron." << G4endl;
        particle = G4ParticleTable::GetParticleTable()->FindParticle("e-");
        fParticleGun->SetParticleDefinition(particle);
    }
    fParticleGun->SetParticleEnergy(energyVal * MeV);
    fParticleGun->SetParticleMomentumDirection(G4ThreeVector(1., 0., 0.));
    fParticleGun->SetParticlePosition(G4ThreeVector(-5.0 * cm, 0.0 * cm, 0.0 * cm));
}

PrimaryGeneratorAction::~PrimaryGeneratorAction() {
    delete fParticleGun;
    fParticleGun = nullptr;
}

void PrimaryGeneratorAction::GeneratePrimaries(G4Event* event) {
    fParticleGun->GeneratePrimaryVertex(event);
}