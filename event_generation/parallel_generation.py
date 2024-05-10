import ROOT
from pythia8 import Pythia
from particle.pdgid import is_hadron
from particle import Particle
import multiprocessing

def is_prompt(event, index):
    # B_hadron_list = [511, 521, 531, 541, 545, 5122, 5112, 5222, 5232, 5132, 5332]
    B_hadron_list = [
        511,
        521,
        10511,
        10521,
        513,
        523,
        10513,
        10523,
        20513,
        20523,
        515,
        525,
        531,
        10531,
        533,
        10533,
        20533,
        535,
        541,
        10541,
        543,
        10543,
        20543,
        545,
    ]
    while event[index].mother1() != 0:
        index = event[index].mother1()
        id_abs = abs(event[index].id())

        if id_abs in B_hadron_list:  # Non-prompt, coming from a b-hadron decay

            # print(Particle.from_pdgid(id_abs), is_hadron(id_abs))
            return 0
        else:
            return 1  # Prompt, no hadron ancestor

    # return 1  # Prompt, no hadron ancestor


def run_pythia(seed, output_file):
    # Initialize Pythia
    pythia = Pythia()

    # Configuration strings
    pythia.readString("Beams:idA = 2212")  # id for protons
    pythia.readString("Beams:idB = 2212")  # id for protons
    pythia.readString("Beams:eCM = 7000.")  # center-of-mass energy in GeV

    pythia.readString("HardQCD:all = on")    # Enable hard QCD processes
    pythia.readString("HadronLevel:All = on")  # Hadronization and decay

    pythia.readString("ParticleDecays:limitTau0 = on")  # Decay particles with c*tau < 10 mm
    pythia.readString("ParticleDecays:tau0Max = 10") 
    pythia.readString("PhaseSpace:pTHatMin= 0.5")
    #pythia.readString("PhaseSpace:pTHatMax= 30.")

    # pythia.readString("Onia:all  = on")
    pythia.readString("Charmonium:all  = on")
    pythia.readString("Bottomonium:all = on")
    pythia.readString("Beams:allowVertexSpread=on")
    # pythia.readString("Charmonium:gg2ccbar(3S1)[3S1(1)]g = on");    # gg -> J/psi g
    # pythia.readString("Charmonium:qqbar2ccbar(3S1)[3S1(1)]g = on"); # qqbar -> J/psi gx

    # pythia.readString("531:onMode = off"); # no B_s0 decay
    # pythia.readString("511:onMode = off"); # no B0 decay
    # pythia.readString("521:onMode = off")  # no B+ decay


    # pythia.readString("443:onMode = off")       # Turn off all J/Psi decays
    pythia.readString("443:onIfMatch = 13 -13")  # // Enable J/Psi -> mu+ mu-
    
     # Set random seed for reproducibility
    pythia.readString("Random:setSeed = on")
    pythia.readString(f"Random:seed = {seed}")
    
    pythia.init()

    # ROOT file and tree setup
    file = ROOT.TFile(output_file, "RECREATE")
    tree = ROOT.TTree("MuonTree", "Tree containing muon info from J/psi")

    # Tree branches
    muon_px = ROOT.std.vector("float")()
    muon_py = ROOT.std.vector("float")()
    muon_pz = ROOT.std.vector("float")()
    muon_e = ROOT.std.vector("float")()
    is_prompt_jpsi = ROOT.std.vector("int")()

    jpsi_dx = ROOT.std.vector("float")()
    jpsi_dy = ROOT.std.vector("float")()
    jpsi_dz = ROOT.std.vector("float")()

    tree.Branch("jpsi_vx", jpsi_dx)
    tree.Branch("jpsi_vy", jpsi_dy)
    tree.Branch("jpsi_vz", jpsi_dz)

    tree.Branch("muon_px", muon_px)
    tree.Branch("muon_py", muon_py)
    tree.Branch("muon_pz", muon_pz)
    tree.Branch("muon_e", muon_e)
    tree.Branch("is_prompt_jpsi", is_prompt_jpsi)

    num_no_jpsi = 0
    nevents = int(20000)
    n_jpsi = []
    n_prompt = 0
    n_non_prompt = 0

    for i_event in range(nevents):
        if not pythia.next():
            print("not pythia!")
            continue

        num_jpsi = 0

        for i in range(pythia.event.size()):
            if pythia.event[i].id() == 443:  # J/psi particle
                num_jpsi += 1
                is_prompt_jpsi.clear()
                muon_px.clear()
                muon_py.clear()
                muon_pz.clear()
                muon_e.clear()

                jpsi_dx.clear()
                jpsi_dy.clear()
                jpsi_dz.clear()

                if is_prompt(pythia.event, i) == 1:
                    is_prompt_jpsi.push_back(1)
                    n_prompt = n_prompt + 1
                else:
                    is_prompt_jpsi.push_back(0)
                    n_non_prompt = n_non_prompt + 1

                daughter1 = pythia.event[i].daughter1()
                daughter2 = pythia.event[i].daughter2()

                jpsi_dx.push_back(pythia.event[daughter1].xProd())
                jpsi_dy.push_back(pythia.event[daughter1].yProd())
                jpsi_dz.push_back(pythia.event[daughter1].zProd())

                # two daughters are the muon pair
                muon_px.push_back(pythia.event[daughter1].px())
                muon_py.push_back(pythia.event[daughter1].py())
                muon_pz.push_back(pythia.event[daughter1].pz())
                muon_e.push_back(pythia.event[daughter1].e())

                muon_px.push_back(pythia.event[daughter2].px())
                muon_py.push_back(pythia.event[daughter2].py())
                muon_pz.push_back(pythia.event[daughter2].pz())
                muon_e.push_back(pythia.event[daughter2].e())

                tree.Fill()

        n_jpsi.append(num_jpsi)

        if num_jpsi == 0:
            num_no_jpsi = num_no_jpsi + 1

    print(f"{nevents} events are generated. {num_no_jpsi} of them has no J/Psi!")
    print(sum(n_jpsi))
    print("prompt:", n_prompt)
    print("non-prompt", n_non_prompt)

    file.Write()
    file.Close()

def merge_root_files(output_files, merged_file):
    merger = ROOT.TFileMerger(False)
    merger.SetFastMethod(True)
    merger.OutputFile(merged_file)
    for f in output_files:
        merger.AddFile(f)
    merger.Merge(False)

def main():
    n_processes = 20
    jobs = []
    output_files = []

    for process_id in range(n_processes):
        seed = 10000 + process_id * 100   # Unique seed for each process
        output_file = f"JpsiToMuMu_{process_id}.root"
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