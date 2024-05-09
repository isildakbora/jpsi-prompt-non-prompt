import ROOT
from pythia8 import Pythia
from particle.pdgid import is_hadron
from particle import Particle

def is_prompt(event, index):
    while event[index].mother1() != 0:
        index = event[index].mother1()
        id_abs = abs(event[index].id())
        
        if id_abs in [511, 521, 531, 541, 5122, 5112, 5222, 5232, 5132, 5332]: #Non-prompt, coming from a b-hadron decay
            #print(Particle.from_pdgid(id_abs), is_hadron(id_abs))
            return 0   
        else:
            return 1  # Prompt, no hadron ancestor
        
    #return 1  # Prompt, no hadron ancestor

# Initialize Pythia
pythia = Pythia()

# Configuration strings
pythia.readString("Beams:idA = 2212")   # id for protons
pythia.readString("Beams:idB = 2212")   # id for protons
#pythia.readString("HardQCD:all = on")  #  Hard QCD processes
pythia.readString("Beams:eCM = 13000.") # center-of-mass energy in GeV
pythia.readString("PhaseSpace:pTHatMin= 20.")
pythia.readString("PhaseSpace:pTHatMax= 30.")

pythia.readString("Onia:all  = on")
#pythia.readString("Charmonium:all  = on")
#pythia.readString("Bottomonium:all = on")
#pythia.readString("Charmonium:gg2ccbar(3S1)[3S1(1)]g = on");    # gg -> J/psi g
#pythia.readString("Charmonium:qqbar2ccbar(3S1)[3S1(1)]g = on"); # qqbar -> J/psi gx

#pythia.readString("531:onMode = off"); # no B_s0 decay
#pythia.readString("511:onMode = off"); # no B0 decay
#pythia.readString("521:onMode = off")  # no B+ decay


#pythia.readString("443:onMode = off")       # Turn off all J/Psi decays
pythia.readString("443:onIfMatch = 13 -13") # // Enable J/Psi -> mu+ mu-

pythia.init()

# ROOT file setup
file = ROOT.TFile("JpsiToMuMu.root", "RECREATE")
tree = ROOT.TTree("MuonTree", "Tree containing muon info from J/psi")

# Tree branches
muon_px = ROOT.std.vector('float')()
muon_py = ROOT.std.vector('float')()
muon_pz = ROOT.std.vector('float')()
muon_e = ROOT.std.vector('float')()
is_prompt_jpsi = ROOT.std.vector('int')()

jpsi_dx = ROOT.std.vector('float')()
jpsi_dy = ROOT.std.vector('float')()
jpsi_dz = ROOT.std.vector('float')()

tree.Branch("jpsi_vx", jpsi_dx)
tree.Branch("jpsi_vy", jpsi_dy)
tree.Branch("jpsi_vz", jpsi_dz)

tree.Branch("muon_px", muon_px)
tree.Branch("muon_py", muon_py)
tree.Branch("muon_pz", muon_pz)
tree.Branch("muon_e", muon_e)
tree.Branch("is_prompt_jpsi", is_prompt_jpsi)

num_no_jpsi = 0
nevents = int(1e+4)
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
            
            if is_prompt(pythia.event, i)==1:
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
            

            # Assuming the two daughters are the muons
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

pythia.stat()