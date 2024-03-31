#include "Pythia8/Pythia.h"
#include "TFile.h"
#include "TTree.h"

using namespace Pythia8;

bool isPrompt(const Event& event, int index) {
    while (event[index].mother1() != 0) {
        index = event[index].mother1();
        int idAbs = abs(event[index].id());
        if (idAbs > 100) {
            return false; // Non-prompt, coming from a hadron decay
        }
    }
    return true; // Prompt, no hadron ancestor
}

int main() {
    Pythia pythia;
    pythia.readString("Charmonium:all = on");
    pythia.readString("443:onMode = off");
    pythia.readString("443:onIfAny = 13");
    pythia.init(2212, 2212, 13000.);

    // ROOT file setup
    TFile* file = new TFile("JpsiToMuMu.root", "RECREATE");
    TTree* tree = new TTree("MuonTree", "Tree containing muon info from J/psi");

    // Tree branches
    Float_t muonPx[2], muonPy[2], muonPz[2], muonE[2];
    Bool_t isPromptJpsi;

    tree->Branch("muonPx", &muonPx, "muonPx[2]/F");
    tree->Branch("muonPy", &muonPy, "muonPy[2]/F");
    tree->Branch("muonPz", &muonPz, "muonPz[2]/F");
    tree->Branch("muonE", &muonE, "muonE[2]/F");
    tree->Branch("isPromptJpsi", &isPromptJpsi, "isPromptJpsi/O");

    for (int iEvent = 0; iEvent < 1000; ++iEvent) {
        if (!pythia.next()) continue;

        for (int i = 0; i < pythia.event.size(); ++i) {
            if (pythia.event[i].id() == 443) { // J/psi particle
                isPromptJpsi = isPrompt(pythia.event, i);
                int daughter1 = pythia.event[i].daughter1();
                int daughter2 = pythia.event[i].daughter2();

                // Assuming the two daughters are the muons
                muonPx[0] = pythia.event[daughter1].px();
                muonPy[0] = pythia.event[daughter1].py();
                muonPz[0] = pythia.event[daughter1].pz();
                muonE[0] = pythia.event[daughter1].e();

                muonPx[1] = pythia.event[daughter2].px();
                muonPy[1] = pythia.event[daughter2].py();
                muonPz[1] = pythia.event[daughter2].pz();
                muonE[1] = pythia.event[daughter2].e();

                tree->Fill();
            }
        }
    }

    file->Write();
    file->Close();

    pythia.stat();

    delete file;
    return 0;
}
