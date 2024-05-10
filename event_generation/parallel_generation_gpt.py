import multiprocessing
import ROOT
from pythia8 import Pythia

def run_pythia(seed, output_file):
    pythia = Pythia()
    # Configuration for Pythia
    pythia.readString("Beams:idA = 2212")  # id for protons
    pythia.readString("Beams:idB = 2212")  # id for protons
    pythia.readString("Beams:eCM = 7000.")  # center-of-mass energy in GeV
    pythia.readString("HardQCD:all = on")
    pythia.readString("PhaseSpace:pTHatMin= 0.5")
    pythia.readString("PhaseSpace:pTHatMax= 30.")
    pythia.readString("Charmonium:all = on")
    pythia.readString("443:onIfMatch = 13 -13")  # J/Psi to mu+ mu-
    
    # Set random seed for reproducibility
    pythia.readString("Random:setSeed = on")
    pythia.readString(f"Random:seed = {seed}")
    
    pythia.init()

    # ROOT file and tree setup
    file = ROOT.TFile(output_file, "RECREATE")
    tree = ROOT.TTree("MuonTree", "Tree containing muon info from J/psi")

    # Define tree branches
    muon_px = ROOT.std.vector("float")()
    muon_py = ROOT.std.vector("float")()
    muon_pz = ROOT.std.vector("float")()
    muon_e = ROOT.std.vector("float")()
    tree.Branch("muon_px", muon_px)
    tree.Branch("muon_py", muon_py)
    tree.Branch("muon_pz", muon_pz)
    tree.Branch("muon_e", muon_e)

    # Event loop
    nevents = 1000
    for i in range(nevents):
        if not pythia.next():
            continue

        # Reset branch vectors
        muon_px.clear()
        muon_py.clear()
        muon_pz.clear()
        muon_e.clear()

        for i in range(pythia.event.size()):
            part = pythia.event[i]
            if part.idAbs() == 443:  # J/psi ID
                daughters = pythia.event.daughterList(i)
                for d in daughters:
                    if pythia.event[d].idAbs() == 13:  # Muon ID
                        muon_px.push_back(pythia.event[d].px())
                        muon_py.push_back(pythia.event[d].py())
                        muon_pz.push_back(pythia.event[d].pz())
                        muon_e.push_back(pythia.event[d].e())

        tree.Fill()

    # Finalize
    file.Write()
    file.Close()
    pythia.stat()

def merge_root_files(output_files, merged_file):
    merger = ROOT.TFileMerger(False)
    merger.SetFastMethod(True)
    for f in output_files:
        merger.AddFile(f)
    merger.Merge(merged_file)

def main():
    n_processes = 10
    jobs = []
    output_files = []

    for i in range(n_processes):
        seed = 10000 + i  # Unique seed for each process
        output_file = f"JpsiToMuMu_{i}.root"
        output_files.append(output_file)
        p = multiprocessing.Process(target=run_pythia, args=(seed, output_file))
        jobs.append(p)
        p.start()

    for job in jobs:
        job.join()

    # Merge the ROOT files into one
    merge_root_files(output_files, "Merged_JpsiToMuMu.root")

if __name__ == "__main__":
    main()
