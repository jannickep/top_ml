# Jannicke Pearkes
# Test code for looking at the samples 
# Plot, debug, loop, extract modes 

import ROOT
from pprint import pprint
import math
import numpy as np
import itertools as IT
from ROOT import gROOT
import re
import sys
import logging as l
import pdg_dictionary
from pdg_dictionary import pdgid_to_name

def regex_search(file_name, regex):
  search = re.compile(regex) 
  value = search.search(file_name)
  return value

def parse_file_name(file_name):
  output_file_name = ""

  jzxw = regex_search(file_name,'(JZ\dW)')
  zprimexxx = regex_search(file_name,'(zprime\d+)')
  daod_num = regex_search(file_name,'(\d+).pool.root')
  
  if(jzxw):
     output_file_name = "dijet"+jzxw.group(1)
  elif(zprimexxx):
     output_file_name = zprimexxx.group(1)
  output_file_name = "outputs/"+output_file_name+"_"+daod_num.group(1)+"tests.root"

  l.info("Output file:"+output_file_name)
  return output_file_name

def sort_topos(topos):
  topo_list = [None]*(topos.size())
  topo_list = [topos.at(topo) for topo in xrange(topos.size())]
  topo_list.sort(key=lambda topo: topo.pt(), reverse=True)
  return topo_list

def delta_r_match(p4_1, p4_2, delta_r_max):
  delta_r = p4_1.DeltaR(p4_2)
  if(delta_r<delta_r_max):
    return True
  else:
    return False 

def get_w(truth):
    W = None
    b = None
    l_truth.debug("Number of children: "+str(truth.nChildren()))
    for i in xrange(truth.nChildren()):
        l_truth.debug("----"+str(pdgid_to_name(truth.child(i).pdgId())))
        if(truth.child(i).isTop()):
            get_w(truth.child(i)) # iterate recursively
        if(truth.child(i).pdgId() == 24):
            l_truth.debug("W filled")
            W = truth.child(i) 
            w_daughters(W)  
        if(truth.child(i).pdgId() == 5):
            l_truth.debug("b filled")
            b = truth.child(i)
    if(W and b):
        return W,b
    return None, None

def get_w_minus(truth):
    W = None
    b = None
    l_truth.debug("Number of children: "+str(truth.nChildren()))
    for i in xrange(truth.nChildren()):
        l_truth.debug("----"+str(pdgid_to_name(truth.child(i).pdgId())))
        if(truth.child(i).isTop()):
            get_w(truth.child(i)) # iterate recursively
        if(truth.child(i).pdgId() == -24):
            l_truth.debug("W filled")
            W = truth.child(i)   
        if(truth.child(i).pdgId() == -5):
            l_truth.debug("b filled")
            b = truth.child(i)
    if(W and b):
        return W,b
    return None, None

def w_daughters(truth):
  x = []
  l_truth.debug("---- W children"+str(truth.nChildren()))
  for i in xrange(truth.nChildren()):
      l_truth.debug("---- ----"+str(pdgid_to_name(truth.child(i).pdgId())))
      if(truth.child(i).isW()):
          x = w_daughters(truth.child(i)) # iterate recursively
      elif (truth.child(i).isQuark()):
          x.append(truth.child(i))
  l_truth.debug("x = "+str(x
    ))
      #if(truth.child(i).isHadron()): 
  return x

def get_z(truth):
    z = truth
    for i in xrange(truth.nChildren()):
        l_truth.debug("----"+str(pdgid_to_name(truth.child(i).pdgId())))
        if(truth.child(i).pdgId() == 32):
            z = get_z(truth.child(i)) # iterate recursively
    return z

def calculate_delta_r_from_particle(W,truth):
    delta_r = W.p4().DeltaR(truth.p4())
    return delta_r

def debug_string_particle(truth):       
    string = pdgid_to_name(truth.pdgId())+(": pt = %g, eta = %g, phi = %g" % (truth.pt(), truth.eta(), truth.phi()))
    return string

def debug_string(truth):       
    string = ": pt = %g, eta = %g, phi = %g" % (truth.pt(), truth.eta(), truth.phi())
    return string

def print_truth_info(z):
  l_truth.debug("Name:"+pdgid_to_name(z.pdgId()))
  l_truth.debug("Status"+str(z.status()))
  l_truth.debug("Barcode:"+str(z.barcode()))
  l_truth.debug("Index:"+str(z.index()))


def traverse_daods(file_name):
    # Constants
    GeV = 1000.
    max_size = 0
    max_index = 0
    count = 0



    gROOT.ProcessLine (".x $ROOTCOREDIR/scripts/load_packages.C");  
    output_file_name = parse_file_name(file_name)
    treeName = "CollectionTree" # default when making transient tree anyway
    f = ROOT.TFile.Open(file_name)
    t = ROOT.xAOD.MakeTransientTree(f, treeName)    
    f_out = ROOT.TFile(output_file_name, "recreate")   

    # Set up histograms if desired
    fill_histograms = 0
    
    eta_range = (-3, 3) 
    phi_range = (-math.pi, math.pi)
    eta_block_size = 0.1
    phi_block_size = 0.1
    n_bins_eta = int((eta_range[1]-eta_range[0])/eta_block_size)
    n_bins_phi = int((phi_range[1]-phi_range[0])/phi_block_size) 
    '''
    if(fill_histograms):
 
      h_num_jets = ROOT.TH1F('num_jets','Number of jets per event',30,0.0,30.0)
      h_num_jets.GetXaxis().SetTitle("Number of jets") 

      h_num_valid_jets = ROOT.TH1F('num_valid_jets','Number of valid jets per event',30,0.0,30.0)
      h_num_valid_jets.GetXaxis().SetTitle("Number of jets") 

      # Jet histograms
      h_jet_pt = ROOT.TH1F('jet_pt','Transverse momentum of all jets',100,0.0,5.0e3)
      h_jet_pt.GetXaxis().SetTitle("p_t [GeV]") 

      h_jet_eta = ROOT.TH1F('jet_eta','Eta distribution for all jets',n_bins_eta,eta_range[0],eta_range[1])
      h_jet_eta.GetXaxis().SetTitle("Eta") 

      h_jet_phi = ROOT.TH1F('jet_phi','Phi distribution for all jets',n_bins_phi,phi_range[0],phi_range[1])
      h_jet_phi.GetXaxis().SetTitle("Phi [rad]") 
      
      h_jet_frac_pt = ROOT.TH1F('jet_frac_pt','Fractional pt carried by all jets',100,0,1)
      h_jet_frac_pt.GetXaxis().SetTitle("Fractional pt")

      h_num_topos = ROOT.TH1F('num_topos','Number of topoclusters per jet',100,0.0,100)
      h_num_topos.GetXaxis().SetTitle("Number of topoclusters") 

      num_jets_to_plot = 6
      h_jet_frac_i = [ROOT.TH1F('jet_frac'+str(i),'Fractional pt carried by jet #'+str(i),100,0,1) for i in xrange(num_jets_to_plot)]
      h_jet_pt_i = [ROOT.TH1F('jet_pt'+str(i),'Pt of jet #'+str(i),100,0.0,5e3) for i in xrange(num_jets_to_plot)]
      h_jet_phi_i = [ROOT.TH1F('jet_phi'+str(i),'Phi of jet #'+str(i),n_bins_phi,phi_range[0],phi_range[1]) for i in xrange(num_jets_to_plot)]
      h_jet_eta_i = [ROOT.TH1F('jet_eta'+str(i),'Eta of jet #'+str(i),n_bins_eta,eta_range[0],eta_range[1]) for i in xrange(num_jets_to_plot)]
      for i in xrange(num_jets_to_plot): 
        h_jet_frac_i[i].GetXaxis().SetTitle("Fractional pt") 
        h_jet_pt_i[i].GetXaxis().SetTitle("p_t [MeV]") 
        h_jet_phi_i[i].GetXaxis().SetTitle("Phi [rad]")  
        h_jet_eta_i[i].GetXaxis().SetTitle("Eta") 

      # Topo histograms
      h_topo_pt = ROOT.TH1F('topo_pt','Pt distribution of all jet constituents',100,-10.0,300000.0)
      h_topo_pt.GetXaxis().SetTitle("p_t [MeV]")  

      h_topo_eta = ROOT.TH1F('topo_eta','Eta distribution of all jet constituents',n_bins_eta,eta_range[0],eta_range[1])
      h_topo_eta.GetXaxis().SetTitle("Eta")  

      h_topo_phi = ROOT.TH1F('topo_phi','Phi distribution of all jet constituents',n_bins_phi,phi_range[0],phi_range[1])
      h_topo_phi.GetXaxis().SetTitle("Phi [rad]")  

      h_topo_frac_pt = ROOT.TH1F('topo_frac_pt','Fractional transverse momentum carried by all jet constituents',100,0,1)
      h_topo_frac_pt.GetXaxis().SetTitle("Fractional pt") 

      num_topos_to_plot = 21
      h_topo_frac_i = [ROOT.TH1F('topo_frac'+str(i),'Fractional pt carried by jet constituent #'+str(i),100,0,1) for i in xrange(num_topos_to_plot)]
      h_topo_pt_i = [ROOT.TH1F('topo_pt'+str(i),'Pt of jet constituent #'+str(i),100,0.0,5e3) for i in xrange(num_topos_to_plot)]
      h_topo_phi_i = [ROOT.TH1F('topo_phi'+str(i),'Phi of jet constituent #'+str(i),n_bins_phi,phi_range[0],phi_range[1]) for i in xrange(num_topos_to_plot)]
      h_topo_eta_i = [ROOT.TH1F('topo_eta'+str(i),'Eta of jet constituent #'+str(i),n_bins_eta,eta_range[0],eta_range[1]) for i in xrange(num_topos_to_plot)]
      
      for i in xrange(num_topos_to_plot): 
        h_topo_frac_i[i].GetXaxis().SetTitle("Fractional pt") 
        h_topo_pt_i[i].GetXaxis().SetTitle("p_t [MeV]") 
        h_topo_phi_i[i].GetXaxis().SetTitle("Phi [rad]")  
        h_topo_eta_i[i].GetXaxis().SetTitle("Eta") 

      eta_range_2 = (-1, 1)
      phi_range_2 = (-1, 1)
      eta_block_size_2 = 0.01
      phi_block_size_2 = 0.01
      n_bins_eta_2 = int((eta_range_2[1]-eta_range_2[0])/eta_block_size_2)
      n_bins_phi_2 = int((phi_range_2[1]-phi_range_2[0])/phi_block_size_2)  

      h_calo_towers = ROOT.TH2F('calo_towers','Calorimeter towers from all jets',
        n_bins_phi_2, phi_range_2[0], phi_range_2[1],
        n_bins_eta_2, eta_range_2[0], eta_range_2[1])
      h_calo_towers.GetXaxis().SetTitle(" Phi  [rad] ")
      h_calo_towers.GetYaxis().SetTitle(" Eta   ")
      h_calo_towers.GetZaxis().SetTitle(" pt [MeV]  ")
    '''

    h_delta_r = ROOT.TH1F('delta_r','Delta R between truth top quarks',30,0,2*math.pi)
    h_delta_r.GetXaxis().SetTitle("Delta R") 
   
    h_delta_r_top_W = ROOT.TH1F('h_delta_r_top_W','Delta R between Top and W',100,0,math.pi)
    h_delta_r_top_W.GetXaxis().SetTitle("$\Delta R$") 

    h_delta_r_top_W_2d = ROOT.TH2F('h_delta_r_top_W_2d','Delta R between Top and W',100,0,2200,100,0,2)
    h_delta_r_top_W_2d.GetXaxis().SetTitle("$p_T^{top}$ [GeV]") 
    h_delta_r_top_W_2d.GetYaxis().SetTitle("$\Delta$ R")
    #h_delta_r_top_W_2d.GetZaxis().SetTitle(" ")

    h_delta_r_top_W_daughters_2d = ROOT.TH2F('h_delta_r_top_W_daughters_2d','Delta R between Top and W-daughters',100,0,2200,100,0,2)
    h_delta_r_top_W_daughters_2d.GetXaxis().SetTitle("$p_T^{top}$ [GeV]") 
    h_delta_r_top_W_daughters_2d.GetYaxis().SetTitle("$\Delta$ R")
    #h_delta_r_top_W_2d.GetZaxis().SetTitle(" ")

    h_delta_r_top_b = ROOT.TH1F('h_delta_r_top_b','Delta R between Top and b',100,0,math.pi)
    h_delta_r_top_b.GetXaxis().SetTitle("$\Delta$ R") 

    h_delta_r_top_b_2d = ROOT.TH2F('h_delta_r_top_b_2d','Delta R between Top and b',100,0,2200,100,0,2)
    h_delta_r_top_b_2d.GetXaxis().SetTitle("$p_T^{top}$ [GeV]") 
    h_delta_r_top_b_2d.GetYaxis().SetTitle("$\Delta$ R")
    #h_delta_r_top_W_2d.GetZaxis().SetTitle(" ")

    h_delta_r_jet_W_2d = ROOT.TH2F('h_delta_r_jet_W_2d','Delta R between Top Jet and W',100,0,2200,100,0,2)
    h_delta_r_jet_W_2d.GetXaxis().SetTitle("$p_T^{jet}$ [GeV]") 
    h_delta_r_jet_W_2d.GetYaxis().SetTitle("$\Delta$ R")
    #h_delta_rjetp_W_2d.GetZaxis().SetTitle(" ")
    h_delta_r_jet_W_daughters_2d = ROOT.TH2F('h_delta_r_jet_W_daughters_2d','Delta R between Jet and W-daughters',100,0,2200,100,0,2)
    h_delta_r_jet_W_daughters_2d.GetXaxis().SetTitle("$p_T^{jet}$ [GeV]") 
    h_delta_r_jet_W_daughters_2d.GetYaxis().SetTitle("$\Delta$ R")
    #h_delta_rjetp_W_2d.GetZaxis().SetTitle(" ")
    h_delta_r_jet_b_2d = ROOT.TH2F('h_delta_r_jet_b_2d','Delta R between Jet and b',100,0,2200,100,0,2)
    h_delta_r_jet_b_2d.GetXaxis().SetTitle("$p_T^{jet}$ [GeV]") 
    h_delta_r_jet_b_2d.GetYaxis().SetTitle("$\Delta$ R")

    h_z_prime_pt = ROOT.TH1F('h_z_prime_pt','Pt of Z prime',100,0.0,4.0e3)
    h_z_prime_pt.GetXaxis().SetTitle("Pt [GeV]") 

    h_z_prime_eta = ROOT.TH1F('h_z_prime_eta','Eta distribution of Z prime',n_bins_eta,eta_range[0],eta_range[1])
    h_z_prime_eta.GetXaxis().SetTitle("Eta")  

    h_z_prime_phi = ROOT.TH1F('h_z_prime_phi','Phi distribution of Z prime',n_bins_phi,phi_range[0],phi_range[1])
    h_z_prime_phi.GetXaxis().SetTitle("Phi [rad]") 

    h_top_match =  ROOT.TH1F('delta_r_top_jet','Delta R between truth top quark and jet',n_bins_phi,0,2*math.pi)
    h_delta_r.GetXaxis().SetTitle("Delta R") 
    
    l.info( "Number of input events: %s" % t.GetEntries())
    
    # Loop over all events
    for entry in xrange(t.GetEntries()): #2000):#
      
      t.GetEntry(entry)
      l.debug( " ################ Run #%i, Event #%i ###########################" % ( t.EventInfo.runNumber(), t.EventInfo.eventNumber() ) )
      l.debug( "Number of jets: %i" %  t.AntiKt10LCTopoTrimmedPtFrac5SmallR20Jets.size() )
      if(entry % 100 == 0 and entry != 0):
        l.info("Processing event: "+str(entry))
      
      # Extract the truth particles from the list 
      l_truth.debug("Number of truth particles:"+str(t.TruthParticles.size()))
      z = None
      top = None
      anti_top = None# Get the last particle in the list
      W_plus = None
      W_minus = None
      b_plus = None
      b_minus = None
      for i in xrange(t.TruthParticles.size()):   
          truth =  t.TruthParticles.at(i)
          if(truth.pdgId() == 32): # Z' 
            z = truth
            #print_truth_info(z) 
            #l_truth.debug(debug_string_particle(z))
          if(truth.pdgId() == 6):
            top = truth
            #print_truth_info(top)
            #l_truth.debug(debug_string_particle(top))
          if(truth.pdgId() == -6):
            anti_top = truth
            #print_truth_info(anti_top)
            #l_truth.debug(debug_string_particle(anti_top))
      '''
      l_truth.debug("Final----")
      print_truth_info(z)
      l_truth.debug(debug_string_particle(z))
      print_truth_info(top)
      l_truth.debug(debug_string_particle(top))
      print_truth_info(anti_top)
      l_truth.debug(debug_string_particle(anti_top))
      '''
      # Fill histograms for truth particles
      if(top):
          truth_top_p4 = top.p4()
          l_truth.debug(debug_string_particle(top))
          W_plus,b_minus = get_w(top)
          if(W_plus and b_minus):
              delta_r_W_top = calculate_delta_r_from_particle(W_plus,top)
              delta_r_b_top = calculate_delta_r_from_particle(b_minus,top)

              h_delta_r_top_W.Fill(delta_r_W_top)
              h_delta_r_top_W_2d.Fill(top.pt()/GeV,delta_r_W_top,1)

              h_delta_r_top_b.Fill(delta_r_b_top)
              h_delta_r_top_b_2d.Fill(top.pt()/GeV,delta_r_b_top,1)
              [l_truth.debug(calculate_delta_r_from_particle(i,top)) for i in w_daughters(W_plus)]
              [h_delta_r_top_W_daughters_2d.Fill(top.pt()/GeV,calculate_delta_r_from_particle(i,top),1) for i in w_daughters(W_plus)]


      if(anti_top):
          truth_anti_top_p4 = anti_top.p4()
          l_truth.debug(debug_string_particle(anti_top))
          if(anti_top.isTop()):
            W_minus,b_plus = get_w_minus(anti_top)
            if(W_minus and b_plus):
              delta_r_W_top = calculate_delta_r_from_particle(W_minus,anti_top)
              delta_r_b_top = calculate_delta_r_from_particle(b_plus,anti_top)

              h_delta_r_top_W.Fill(delta_r_W_top)
              h_delta_r_top_W_2d.Fill(anti_top.pt()/GeV,delta_r_W_top,1)

              h_delta_r_top_b.Fill(delta_r_b_top)
              h_delta_r_top_b_2d.Fill(anti_top.pt()/GeV,delta_r_b_top,1)

              [l_truth.debug(calculate_delta_r_from_particle(i,anti_top)) for i in w_daughters(W_minus)]
              [h_delta_r_top_W_daughters_2d.Fill(anti_top.pt()/GeV,calculate_delta_r_from_particle(i,anti_top),1) for i in w_daughters(W_minus)]

      if(top and anti_top):
        delta_r = anti_top.p4().DeltaR(top.p4())
        h_delta_r.Fill(delta_r)
      
      if(z):
          l_truth.debug("Z': pt = %g, eta = %g, phi = %g" % (z.pt(), z.eta(), z.phi()))
          h_z_prime_pt.Fill(z.pt()/GeV) 
          h_z_prime_eta.Fill(z.eta())
          h_z_prime_phi.Fill(z.phi())
      
      #for i in xrange(t.AntiKt10TruthJets.size()):
      #    truth_jet = t.AntiKt10TruthJets.at(i)
      #    print("Parton truth label id:"+str(truth_jet.PartonTruthLabelID)) #nope
          #print("ConeTruthLabelID:"+str(truth_jet.ConeTruthLabelID())) #nope
          #print("PdgID:"+str(truth_jet.pdgId()))
      '''
      if(fill_histograms):
        h_num_jets.Fill(t.AntiKt10LCTopoTrimmedPtFrac5SmallR20Jets.size()) 
      
      # Calculate total jet pt
      total_jet_pt = 0
      for i in xrange(t.AntiKt10LCTopoTrimmedPtFrac5SmallR20Jets.size()):
        total_jet_pt += t.AntiKt10LCTopoTrimmedPtFrac5SmallR20Jets.at(i).pt() 
     '''
      # Loop over all jets in an event
      valid_jets = 0
      '''
      first_jet = t.AntiKt10LCTopoTrimmedPtFrac5SmallR20Jets.at(0)
      closest_match_to_top = calculate_delta_r_from_particle(top,first_jet)
      closest_match_to_anti_top = calculate_delta_r_from_particle(anti_top,first_jet)
      jet_top_match = 0
      jet_anti_top_match = 0
      '''
      for i in xrange(t.AntiKt10LCTopoTrimmedPtFrac5SmallR20Jets.size()):
        if(t.AntiKt10LCTopoTrimmedPtFrac5SmallR20Jets.at(i).pt()>=150e3 and abs(t.AntiKt10LCTopoTrimmedPtFrac5SmallR20Jets.at(i).eta())< 2.7):
          valid_jets += 1
          jet = t.AntiKt10LCTopoTrimmedPtFrac5SmallR20Jets.at(i) 
          '''
          if(fill_histograms):
            if (i<=5):
                h_jet_frac_i[i].Fill(jet.pt()/total_jet_pt) 
                h_jet_pt_i[i].Fill(jet.pt()/GeV)
                h_jet_eta_i[i].Fill(jet.eta())  
                h_jet_phi_i[i].Fill(jet.phi())
            h_jet_pt.Fill(jet.pt()/GeV)
            h_jet_frac_pt.Fill(jet.pt()/total_jet_pt)
            h_jet_phi.Fill(jet.phi())
            h_jet_eta.Fill(jet.eta())
          '''
          match_to_top = calculate_delta_r_from_particle(top,jet)
          if(match_to_top<closest_match_to_top):
              closest_match_to_top = match_to_top 
              jet_top_match = i

          match_to_anti_top = calculate_delta_r_from_particle(anti_top,jet)
          if(match_to_anti_top<closest_match_to_anti_top):
              closest_match_to_anti_top = match_to_anti_top 
              jet_anti_top_match = i

          l_jet.info("Jet "+str(i)+"-------------------------------------")
          l_jet.info(debug_string(jet))
          matches_top = False
          matches_top = delta_r_match(top.p4(), jet.p4(), 0.4)
          if (matches_top and top and W_plus and b_minus):
              l_jet.debug("Jet "+str(i)+" matches top")
              h_delta_r_jet_b_2d.Fill(jet.pt()/GeV,calculate_delta_r_from_particle(b_minus,jet),1)
              h_delta_r_jet_W_2d.Fill(jet.pt()/GeV,calculate_delta_r_from_particle(W_plus,jet),1)
              l_truth.debug("top delta r:")
              l_truth.debug("jet p4:"+str(jet.p4()))
              l_truth.debug("W child:"+str(W_plus.child(0)))
              [l_truth.debug(calculate_delta_r_from_particle(q,jet)) for q in w_daughters(W_plus)]
              [h_delta_r_jet_W_daughters_2d.Fill(jet.pt()/GeV,calculate_delta_r_from_particle(q,jet),1) for q in w_daughters(W_plus)]
            
          h_top_match.Fill(top.p4().DeltaR(jet.p4()))
          matches_anti_top = False
          matches_anti_top = delta_r_match(anti_top.p4(), jet.p4(), 0.4)
          if(matches_anti_top and anti_top and W_minus and b_plus):
            l_jet.debug("Jet "+str(i)+" matches anti-top")
            h_delta_r_jet_b_2d.Fill(jet.pt()/GeV,calculate_delta_r_from_particle(b_plus,jet),1)
            h_delta_r_jet_W_2d.Fill(jet.pt()/GeV,calculate_delta_r_from_particle(W_minus,jet),1)
            l_truth.debug("anti-top delta r:")
            l_truth.debug("jet p4:"+str(jet.p4()))
            [l_truth.debug(calculate_delta_r_from_particle(q,jet)) for q in w_daughters(W_minus)]
            [h_delta_r_jet_W_daughters_2d.Fill(jet.pt()/GeV,calculate_delta_r_from_particle(q,jet),1) for q in w_daughters(W_minus)]

          '''
          topos = jet.getConstituents()

        
          # Loop over all jet constituents
          l_jet_sub.info("Size of topos: "+str(topos.size())+", Valid? "+str(topos.isValid())) #roughly half of these are invalid
          if(fill_histograms):
            h_num_topos.Fill(topos.size())
          if(topos.isValid()):
              topos = sort_topos(topos)
              # calculate total pt from topoclusters first (needed for fractional pt)
              jet_pt_from_topos = 0
              for index in xrange(len(topos)):
                    topo = topos[index]#
                    jet_pt_from_topos += topo.pt()
              # loop over topoclusters
              for index in xrange(len(topos)):
                    topo = topos[index]# #topos[index] topos.at(index)#
                    l_jet_sub.info(debug_string(topo))
                    l_jet_sub.debug(dir(topo))
                    raw_cluster = topo.rawConstituent()
                    l_jet_sub.debug( "Raw Cluster: "+debug_string(raw_cluster))    
                    l_jet_sub.debug(dir(raw_cluster))
                    if(fill_histograms):
                      h_calo_towers.Fill(topo.eta()-jet.eta(), topo.phi()-jet.phi(),topo.pt())# for i in xrange(5)] # before transformations
                      h_topo_pt.Fill(topo.pt()) 
                      h_topo_phi.Fill(topo.phi()) 
                      h_topo_eta.Fill(topo.eta()) 
                      h_topo_frac_pt.Fill(topo.pt()/jet.pt())
                      if (index <num_topos_to_plot):
                          h_topo_frac_i[index].Fill(topo.pt()/jet_pt_from_topos) 
                          h_topo_pt_i[index].Fill(topo.pt()/GeV)
                          h_topo_eta_i[index].Fill(topo.eta())  
                          h_topo_phi_i[index].Fill(topo.phi())         

              l_jet_sub.debug("Jet_pt from Jet   = %g" % jet.pt())
              l_jet_sub.debug("Jet_pt from Topos = %g" % jet_pt_from_topos)
      if(fill_histograms):
        h_num_valid_jets.Fill(valid_jets)
    '''
    f_out.Write()
    f_out.Close()
    f.Close()  
    ROOT.xAOD.ClearTransientTrees() 

if __name__ == '__main__':
    # setup loggers 
    l.basicConfig(level=l.INFO, format='%(levelname)s - %(message)s')#%(asctime)s - %(levelname)s - %(message)s')
    l_jet = l.getLogger("jet logger")
    l_jet.setLevel(l.ERROR)
    #l_jet.setLevel(l.DEBUG)
    l_jet_sub = l.getLogger("jet sub logger")
    l_jet_sub.setLevel(l.ERROR)
    #l_jet_sub.setLevel(l.DEBUG)
    l_truth = l.getLogger("truth logger")
    l_truth.setLevel(l.ERROR)
    #l_truth.setLevel(l.DEBUG)

    # read in filename as input
    if len(sys.argv)>=2:
      name,file_name = sys.argv
    else:
      # zprime tt 400
      #file_name = "/data/wfedorko/mc15_13TeV.301322.Pythia8EvtGen_A14NNPDF23LO_zprime400_tt.merge.DAOD_EXOT7.e4061_s2608_s2183_r7326_r6282_p2495_tid07896478_00/DAOD_EXOT7.07896478._000001.pool.root.1"
      # zprime tt 1000
      #file_name = "/data/wfedorko/mc15_13TeV.301325.Pythia8EvtGen_A14NNPDF23LO_zprime1000_tt.merge.DAOD_EXOT7.e4061_s2608_s2183_r7326_r6282_p2495_tid07618490_00/DAOD_EXOT7.07618490._000001.pool.root.1"
      # zprime tt 2000
      #file_name = "/data/wfedorko/mc15_13TeV.301329.Pythia8EvtGen_A14NNPDF23LO_zprime2000_tt.merge.DAOD_EXOT7.e4061_s2608_s2183_r7326_r6282_p2495_tid07618440_00/DAOD_EXOT7.07618440._000001.pool.root.1"
      # zprime tt 2250
      #file_name = "/data/wfedorko/mc15_13TeV.301330.Pythia8EvtGen_A14NNPDF23LO_zprime2250_tt.merge.DAOD_EXOT7.e4061_s2608_s2183_r7326_r6282_p2495_tid07618509_00/DAOD_EXOT7.07618509._000010.pool.root.1"
      # zprime tt 3000
      #file_name = "/data/wfedorko/mc15_13TeV.301333.Pythia8EvtGen_A14NNPDF23LO_zprime3000_tt.merge.DAOD_EXOT7.e3723_s2608_s2183_r7326_r6282_p2495_tid07618517_00/DAOD_EXOT7.07618517._000001.pool.root.1"
      # zprime tt 4000
      file_name = "/data/wfedorko/mc15_13TeV.301334.Pythia8EvtGen_A14NNPDF23LO_zprime4000_tt.merge.DAOD_EXOT7.e3723_s2608_s2183_r7326_r6282_p2495_tid07618446_00/DAOD_EXOT7.07618446._000001.pool.root.1"
      # zprime tt 5000
      #file_name = "/data/wfedorko/mc15_13TeV.301335.Pythia8EvtGen_A14NNPDF23LO_zprime5000_tt.merge.DAOD_EXOT7.e3723_s2608_s2183_r7326_r6282_p2495_tid07618499_00/DAOD_EXOT7.07618499._000005.pool.root.1"
      # dijet 
      #file_name = "/data/wfedorko/mc15_13TeV.361022.Pythia8EvtGen_A14NNPDF23LO_jetjet_JZ2W.merge.DAOD_EXOT7.e3668_s2576_s2132_r7267_r6282_p2495_tid07618436_00/DAOD_EXOT7.07618436._000001.pool.root.1"
    l.info("Input file: "+file_name)
    traverse_daods(file_name)