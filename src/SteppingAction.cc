#include "SteppingAction.hh"
#include "EventAction.hh"
#include <G4Step.hh>
#include <G4Track.hh>
#include <G4ParticleDefinition.hh>
#include <G4VProcess.hh>
#include <G4SystemOfUnits.hh>
#include <G4PhysicalConstants.hh>
#include <cmath>

SteppingAction::SteppingAction(EventAction* eventAction)
 : fEventAction(eventAction)
{
}

SteppingAction::~SteppingAction() = default;

void SteppingAction::UserSteppingAction(const G4Step* step) {
    G4int currentStep = step->GetTrack()->GetCurrentStepNumber();

    G4StepPoint* prePoint = step->GetPreStepPoint();
    G4VPhysicalVolume* preVol = prePoint->GetPhysicalVolume();
    G4VPhysicalVolume* postVol = step->GetPostStepPoint()->GetPhysicalVolume();

    if (!preVol) return;

    G4String preName = preVol->GetName();
    G4String postName = postVol ? postVol->GetName() : "OutOfWorld";

    if (preName == "Phantom" && postName != "Phantom") {
        step->GetTrack()->SetTrackStatus(fStopAndKill);
        G4double dE = step->GetTotalEnergyDeposit();
        if (dE > 0) fEventAction->AddEnergyDeposit(dE);
        return;
    }

    if (step->GetTrack()->GetTrackID() != 1) {
        HandleSecondaryParticle(step);
        return;
    }

    bool inPhantom = (preName == "Phantom" || postName == "Phantom");
    if (inPhantom) {
        RecordPrimaryParticleStep(step);
    }
}

void SteppingAction::RecordPrimaryParticleStep(const G4Step* step) {
    G4StepPoint* postPoint = step->GetPostStepPoint();

    StepRecord record;
    record.position = postPoint->GetPosition();
    record.momentum = postPoint->GetMomentum();
    record.kineticEnergy = postPoint->GetKineticEnergy();
    record.energyDeposited = step->GetTotalEnergyDeposit();
    
    fEventAction->AddStepRecord(record);
}

void SteppingAction::HandleSecondaryParticle(const G4Step* step) {
    G4double dE = step->GetTotalEnergyDeposit();
    if (dE > 0) {
        G4VPhysicalVolume* preVol = step->GetPreStepPoint()->GetPhysicalVolume();
        if (preVol && preVol->GetName() == "Phantom") {
            fEventAction->AddEnergyDeposit(dE);
        }
    }
}
