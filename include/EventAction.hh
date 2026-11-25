#ifndef EVENT_ACTION_HH
#define EVENT_ACTION_HH

#include <G4UserEventAction.hh>
#include <vector>
#include <G4ThreeVector.hh>

struct StepRecord {
    G4ThreeVector position;
    G4ThreeVector momentum;
    G4double kineticEnergy;
    G4double energyDeposited;
};

class EventAction : public G4UserEventAction {
public:
    EventAction();
    ~EventAction() override;
    void BeginOfEventAction(const G4Event* event) override;
    void EndOfEventAction(const G4Event* event) override;
    void AddStepRecord(const StepRecord& step);
    void AddEnergyDeposit(G4double edep);
    const std::vector<StepRecord>& GetStepRecords() const { return fStepRecords; }
    
private:
    std::vector<StepRecord> fStepRecords;
};

#endif
