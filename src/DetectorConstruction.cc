#include "DetectorConstruction.hh"
#include <G4Box.hh>
#include <G4NistManager.hh>
#include <G4LogicalVolume.hh>
#include <G4PVPlacement.hh>
#include <G4VisAttributes.hh>
#include <G4Colour.hh>
#include <G4SystemOfUnits.hh>
#include <G4Material.hh>
#include <G4UserLimits.hh>
#include <G4ios.hh>
#include <cstdlib>

DetectorConstruction::DetectorConstruction()
 : fPhantomSize(5.0*cm)
 , fWorldSize(15.0*cm)
 , fLogicWorld(nullptr)
 , fLogicPhantom(nullptr)
{
}

DetectorConstruction::~DetectorConstruction() = default;

G4VPhysicalVolume* DetectorConstruction::Construct() {
    G4NistManager* nist = G4NistManager::Instance();
    G4Material* air = nist->FindOrBuildMaterial("G4_AIR");

    const char* matName = std::getenv("DETECTOR_MATERIAL") ? std::getenv("DETECTOR_MATERIAL") : "G4_SODIUM_IODIDE";
    G4Material* detMat = nist ->FindOrBuildMaterial(matName);
    if(!detMat)
    {
        G4cout << "Material " << matName << " not found. Using G4_SODIUM_IODIDE instead." << G4endl;
        detMat = nist ->FindOrBuildMaterial("G4_SODIUM_IODIDE");        
    }

    G4Box* solidWorld = new G4Box("World", fWorldSize, fWorldSize, fWorldSize);
    fLogicWorld = new G4LogicalVolume(solidWorld, air, "World");

    G4VPhysicalVolume* physWorld = new G4PVPlacement(
        nullptr,
        G4ThreeVector(),
        fLogicWorld,
        "World",
        nullptr,
        false,
        0,
        true
    );

    G4Box* solidPhantom = new G4Box("Phantom", fPhantomSize, fPhantomSize, fPhantomSize);
    fLogicPhantom = new G4LogicalVolume(solidPhantom, detMat, "Phantom");

    G4double maxStep = 0.1 * cm; 
    fLogicPhantom->SetUserLimits(new G4UserLimits(maxStep));
    
    new G4PVPlacement(
        nullptr,
        G4ThreeVector(0., 0., 0.),
        fLogicPhantom,
        "Phantom",
        fLogicWorld,
        false,
        0,
        true
    );

    fLogicWorld->SetVisAttributes(G4VisAttributes::GetInvisible());
    
    G4VisAttributes* phantomVis = new G4VisAttributes(G4Colour::Yellow());
    phantomVis->SetForceWireframe(true);
    phantomVis->SetLineWidth(2.0);
    fLogicPhantom->SetVisAttributes(phantomVis);
    
    return physWorld;
}
