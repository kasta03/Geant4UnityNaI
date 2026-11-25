#ifndef STEPPING_ACTION_HH
#define STEPPING_ACTION_HH

#include <G4UserSteppingAction.hh>
#include <G4Step.hh>

class EventAction;

class SteppingAction : public G4UserSteppingAction {
public:
    explicit SteppingAction(EventAction* eventAction);
    ~SteppingAction() override;
    void UserSteppingAction(const G4Step* step) override;
    
private:
    EventAction* fEventAction;
    void RecordPrimaryParticleStep(const G4Step* step);
    void HandleSecondaryParticle(const G4Step* step);
};

#endif
