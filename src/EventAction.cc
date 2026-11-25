#include "EventAction.hh"
#include <G4Event.hh>
#include <G4SystemOfUnits.hh>
#include <G4ios.hh>

EventAction::EventAction() {
    fStepRecords.reserve(1000);
}

EventAction::~EventAction() = default;

void EventAction::BeginOfEventAction(const G4Event* ) {
    fStepRecords.clear();
}

void EventAction::EndOfEventAction(const G4Event* event) {
    G4int eventID = event->GetEventID();
    if (eventID % 100 == 0 || fStepRecords.size() > 0) {
        // G4cout << "Event " << eventID << ": " << fStepRecords.size() << " steps" << G4endl;
    }
}

void EventAction::AddStepRecord(const StepRecord& step) {
    fStepRecords.push_back(step);
}

void EventAction::AddEnergyDeposit(G4double ) {
}
