from pftMgmtWriter import write_pft_mgmt

config_dry_dict={
'case':'dryland',
'mdir':'/Users/jinyuntang/work/github/ecosim2/EcoSIM/examples/inputs/dryland_maize/',
'pftf':'me01p:me02p:me03p:me04p:me05p:me06p',
'year':'2001:2002:2003:2004:2005:2006',
'outdir':'/Users/jinyuntang/work/github/ecosim3/EcoSIM/examples/inputs/dryland_maize/',    
'ntopu':'1',
'ncol':'1',
'nrow':'1'    
}

config_lake_dict={
'case':'lake',
'mdir':'/Users/jinyuntang/work/github/ecosim2/EcoSIM/examples/inputs/lake/',
'pftf':'va99p:vaxxp',
#'topf':'vatopo',
'outdir':'/Users/jinyuntang/work/github/ecosim3/EcoSIM/examples/inputs/lake/',        
'ntopu':'2',
'ncol':'2',
'nrow':'1'
}

config_sample_dict={
'case':'sample',
'mdir':'/Users/jinyuntang/work/github/ecosim2/EcoSIM/examples/inputs/sample/',
'pftf':'pft_arctic_p:pft_arctic_g',
'outdir':'/Users/jinyuntang/work/github/ecosim3/EcoSIM/examples/inputs/sample/',        
'ntopu':'1',
'ncol':'1',
'nrow':'1'
}

config_DaringLake_dict={
'case':'DaringLake',
'mdir':'/Users/jinyuntang/work/github/ecosys2/ecosys_benchmark_runs_2022_oct_24/DaringLake/',
'pftf':'dlmt00p:dlmtxxp',
#'topf':'dlmtto',
'outdir':'./',
'ntopu':'2'
}

config_Fen_StordIsland_dict={
'case':'FenStordIsland',
'mdir':'/Users/jinyuntang/work/ecosys_benchmark/fenrun_shuai/',
'pftf':'sdlxxp2:sdlxxp_no',
#'topf':'dlmtto',
'outdir':'/Users/jinyuntang/work/ecosim_benchmark/smallset/FenStordIsland/',    
'ntopu':'1',
'ncol':'1',
'nrow':'1'

}


config_MeditPastureCA_dict={
'case':'MeditPastureCA',
'mdir':'/Users/jinyuntang/work/ecosys_benchmark/Meditteranean_Pasture_CA/',
'pftf':'va99p:vaxxp',
'outdir':'/Users/jinyuntang/work/ecosim_benchmark/smallset/MeditteraneanPastureCA/',    
#'topf':'dlmtto',
'ntopu':'1',
'ncol':'1',
'nrow':'1'

}

config_US_Ton_dict={
'case':'US_Ton',
'mdir':'/Users/jinyuntang/work/ecosys_benchmark/US_Ton/',
'pftf':'pft_uston_p:pft_uston_g',    
#'topf':'dlmtto',
'outdir':'/Users/jinyuntang/work/ecosim_benchmark/smallset/US_Ton',    
'ntopu':'1',
'ncol':'1',
'nrow':'1'

}


config_SemiaridGrassland_dict={
'case':'SemiaridGrassland',
'mdir':'/Users/jinyuntang/work/ecosys_benchmark/Semiarid_Grassland_AB/',
'pftf':'lepg:lepx',    
'outdir':'/Users/jinyuntang/work/ecosim_benchmark/smallset/SemiaridGrasslandAB/',    
#'topf':'dlmtto',
'ntopu':'1',
'ncol':'1',
'nrow':'1'
}    

config_WarmTempOakTN_dict={
'case':'WarmTempOakTN',
'mdir':'/Users/jinyuntang/work/ecosys_benchmark/Warm_Temperate_Oak_TN/',
'pftf':'td60p:tdxxp',    
'outdir':'/Users/jinyuntang/work/ecosim_benchmark/smallset/WarmTemperateOakTN/',    
'ntopu':'1',
'ncol':'1',
'nrow':'1'
}    


config_SnodgrassTransect_dict={
'case':'SnodgrassTransect',
'mdir':'/Users/jinyuntang/work/github/ecosys_benchmark/Snodgrass_transect/',
'pftf':'pft_ert_p:pft_ert_g',
'outdir':'/Users/jinyuntang/work/github/ecosim_benchmark/smallset/Snodgrass_transect/',    
#'topf':'dlmtto',
'ntopu':'6'
}    


config_Blodget_dict={
'case':'Blodget',
'mdir':'/Users/jinyuntang/work/github/Blodget/',
'pftf':'pftUS_Blo_p_2:pftUS_Blo_g_2',
'outdir':'/Users/jinyuntang/work/github/ecosim_benchmark/smallset/Blodget/',    
'ntopu':'1'
}    

config_Morrow2_dict={
'case':'Morrow2',
'mdir':'/Users/jinyuntang/work/github/ecosys_benchmark/Morrow_figure3/17-2/',
'pftf':'mexxxxp',
'year':'1898-2021',    
'outdir':'/Users/jinyuntang/work/github/ecosim_benchmark/smallset/Morrow2/',    
'ntopu':'1'
}    

config_Morrow4_dict={
'case':'Morrow4',
'mdir':'/Users/jinyuntang/work/github/ecosys_benchmark/Morrow_figure3/17-4/',
'pftf':'mexxxxp',
'year':'1898-2021',    
'outdir':'/Users/jinyuntang/work/github/ecosim_benchmark/smallset/Morrow4/',    
'ntopu':'1'
}    

config_spruces1_dict={
'case':'Spruce-s1',
'mdir':'/Users/jinyuntang/work/github/ecosys_benchmark/spruce_PQ_3PFT_s1/',
'pftf':'spr_p:spr_g',
'outdir':'/Users/jinyuntang/work/github/ecosim_benchmark/Spruce-s1/',    
'ntopu':'1'
}    

config_sorghum_dict={
'case':'Sorghum',
'mdir':'/Users/jinyuntang/work/github/ecosys_benchmark/sorghum/plt_sorg/',
'pftf':'mexxxxp',
'year':'2002-2007',    
'outdir':'/Users/jinyuntang/work/github/ecosim_benchmark/smallset/Sorghum/',    
'ntopu':'1'
}    

config_plm_dict={
'case':'PLM',
'mdir':'/Users/jinyuntang/work/github/ecosys_benchmark/plmrEcosys/',
'pftf':'nlegp1:nlegg1',  
'outdir':'/Users/jinyuntang/work/github/ecosim_benchmark/smallset/PLM/',    
'ntopu':'7'
}    


case=12

if case==1:
    config_dict=config_Fen_StordIsland_dict
elif case==2:    
    config_dict=config_WarmTempOakTN_dict
elif case==3:    
    config_dict=config_US_Ton_dict
elif case==4:    
    config_dict=config_SemiaridGrassland_dict
elif case==5:    
    config_dict=config_MeditPastureCA_dict
elif case==6:
    config_dict=config_SnodgrassTransect_dict
elif case==7:
    config_dict=config_Blodget_dict
elif case==8:
    config_dict=config_Morrow2_dict
elif case==9:
    config_dict=config_Morrow4_dict
elif case==10:
    config_dict=config_spruces1_dict
elif case==11:
    config_dict=config_sorghum_dict
elif case==12:
    config_dict=config_plm_dict
    
write_pft_mgmt(config_dict)

#write topgraphy and site data

"""
main body of code
"""

#topo unit file
config_dry_dict={
'case':'dryland',
'mdir':'/Users/jinyuntang/work/github/ecosim3/EcoSIM/examples/inputs/dryland_maize/',
'sitef':'mesite',
'topf':'metopo',
'outdir':'/Users/jinyuntang/work/github/ecosim3/EcoSIM/examples/inputs/dryland_maize/',        
'ntopu':'1',
'ncol':'1',
'nrow':'1',
'NHW':'1',
'NVN':'1',
'NHE':'1',
'NVS':'1'
}

config_lake_dict={
'case':'lake',
'mdir':'/Users/jinyuntang/work/github/ecosim2/EcoSIM/examples/inputs/lake/',
'sitef':'vasite',
'topf':'vatopo',
'outdir':'/Users/jinyuntang/work/github/ecosim2/EcoSIM/examples/inputs/lake/',
'ntopu':'2',
'ncol':'2',
'nrow':'1',
'NHW':'1',
'NVN':'1',
'NHE':'2',
'NVS':'1'
}

config_sample_dict={
'case':'sample',
'mdir':'/Users/jinyuntang/work/github/ecosim2/EcoSIM/examples/inputs/sample/',
'sitef':'st022852',
'topf':'tp022852',
'outdir':'/Users/jinyuntang/work/github/ecosim2/EcoSIM/examples/inputs/sample/',    
'ntopu':'1',
'ncol':'1',
'nrow':'1',
'NHW':'1',
'NVN':'1',
'NHE':'1',
'NVS':'1'
}


config_DaringLake_dict={
'case':'DaringLake',
'mdir':'/Users/jinyuntang/work/github/ecosys2/ecosys_benchmark_runs_2022_oct_24/DaringLake/',
'sitef':'dlmts',
'outdir':'./',    
'topf':'dlmtto',
'ntopu':'6',
'ncol':'1',
'nrow':'6',
'NHW':'1',
'NVN':'1',
'NHE':'1',
'NVS':'6'
}

config_Fen_StordIsland_dict={
'case':'FenStordIsland',
'mdir':'/Users/jinyuntang/work/ecosys_benchmark/fenrun_shuai/',
'sitef':'sdlsite',
'topf':'sdltopo',
'outdir':'/Users/jinyuntang/work/ecosim_benchmark/smallset/FenStordIsland/',
'ntopu':'1',
'ncol':'1',
'nrow':'1',
'NHW':'1',
'NVN':'1',
'NHE':'1',
'NVS':'1'
}

config_US_Ton_dict={
'case':'US_Ton',
'mdir':'/Users/jinyuntang/work/ecosys_benchmark/US_Ton/',
'sitef':'st_uston',
'topf':'tp_uston',
'outdir':'/Users/jinyuntang/work/ecosim_benchmark/smallset/US_Ton/',    
'ntopu':'1',
'ncol':'1',
'nrow':'1',
'NHW':'1',
'NVN':'1',
'NHE':'1',
'NVS':'1'
}

config_MeditPastureCA_dict={
'case':'MeditPastureCA',
'mdir':'/Users/jinyuntang/work/ecosys_benchmark/Meditteranean_Pasture_CA/',
'sitef':'vasite',
'topf':'vatopo',
'outdir':'/Users/jinyuntang/work/ecosim_benchmark/smallset/MeditteraneanPastureCA/',    
'ntopu':'1',
'ncol':'1',
'nrow':'1',
'NHW':'1',
'NVN':'1',
'NHE':'1',
'NVS':'1'
}

config_SemiaridGrassland_dict={
'case':'SemiaridGrassland',
'mdir':'/Users/jinyuntang/work/ecosys_benchmark/Semiarid_Grassland_AB/',
'sitef':'lsite',
'topf':'ltopo',
'outdir':'/Users/jinyuntang/work/ecosim_benchmark/smallset/SemiaridGrasslandAB/',
'ntopu':'1',
'ncol':'1',
'nrow':'1',
'NHW':'1',
'NVN':'1',
'NHE':'1',
'NVS':'1'
}

config_WarmTempOakTN_dict={
'case':'WarmTempOakTN',
'mdir':'/Users/jinyuntang/work/ecosys_benchmark/Warm_Temperate_Oak_TN/',
'sitef':'tds',
'topf':'tdtopo',
'outdir':'/Users/jinyuntang/work/ecosim_benchmark/smallset/WarmTemperateOakTN',    
'ntopu':'1',
'ncol':'1',
'nrow':'1',
'NHW':'1',
'NVN':'1',
'NHE':'1',
'NVS':'1'
}

config_SnodgrassTransect_dict={
'case':'SnodgrassTransect',
'mdir':'/Users/jinyuntang/work/ecosys_benchmark/Snodgrass_transect/',
'sitef':'st074773_e',
'topf':'tp074773_e',    
'outdir':'/Users/jinyuntang/work/ecosim_benchmark/smallset/Snodgrass_transect',    
'ntopu':'6',
'ncol':'6',
'nrow':'1',
'NHW':'1',
'NVN':'1',
'NHE':'6',
'NVS':'1'
}

config_Blodget_dict={
'case':'Blodget',
'mdir':'/Users/jinyuntang/work/github/Blodget/',
'sitef':'st_1980',
'topf':'tpUS_Blo2',    
'outdir':'/Users/jinyuntang/work/github/ecosim_benchmark/smallset/Blodget/',    
'ntopu':'1',
'ncol':'1',
'nrow':'1',
'NHW':'1',
'NVN':'1',
'NHE':'1',
'NVS':'1'
}

config_Morrow2_dict={
'case':'Morrow2',
'mdir':'/Users/jinyuntang/work/github/ecosys_benchmark/Morrow_figure3/17-2/',
'sitef':'mesite',
'topf':'metopo',    
'outdir':'/Users/jinyuntang/work/github/ecosim_benchmark/smallset/Morrow2/',    
'ntopu':'1',
'ncol':'1',
'nrow':'1',
'NHW':'1',
'NVN':'1',
'NHE':'1',
'NVS':'1'
}

config_Morrow4_dict={
'case':'Morrow4',
'mdir':'/Users/jinyuntang/work/github/ecosys_benchmark/Morrow_figure3/17-4/',
'sitef':'mesite',
'topf':'metopo',    
'outdir':'/Users/jinyuntang/work/github/ecosim_benchmark/smallset/Morrow4/',    
'ntopu':'1',
'ncol':'1',
'nrow':'1',
'NHW':'1',
'NVN':'1',
'NHE':'1',
'NVS':'1'
}

config_spruces1_dict={
'case':'Spruce-s1',
'mdir':'/Users/jinyuntang/work/github/ecosys_benchmark/spruce_PQ_3PFT_s1/',
'sitef':'sprsite',
'topf':'sprtopo',    
'outdir':'/Users/jinyuntang/work/github/ecosim_benchmark/Spruce-s1/',    
'ntopu':'1',
'ncol':'1',
'nrow':'1',
'NHW':'1',
'NVN':'1',
'NHE':'1',
'NVS':'1'
}

config_sorghum_dict={
'case':'Sorghum',
'mdir':'/Users/jinyuntang/work/github/ecosys_benchmark/sorghum/plt_sorg/',
'sitef':'mesite',
'topf':'metopo',    
'outdir':'/Users/jinyuntang/work/github/ecosim_benchmark/smallset/Sorghum/',    
'ntopu':'1',
'ncol':'1',
'nrow':'1',
'NHW':'1',
'NVN':'1',
'NHE':'1',
'NVS':'1'
}


config_PLM_dict={
'case':'PLM',
'mdir':'/Users/jinyuntang/work/github/ecosys_benchmark/plmrEcosys/',
'sitef':'st074773',
'topf':'tp074773',    
'outdir':'/Users/jinyuntang/work/github/ecosim_benchmark/smallset/PLM/',    
'ntopu':'7',
'ncol':'7',
'nrow':'1',
'NHW':'1',
'NVN':'1',
'NHE':'7',
'NVS':'1'
}

from SiteTopoWriter import write_site_topo_data

if case==1:
    config_dict=config_Fen_StordIsland_dict
elif case==2:    
    config_dict=config_WarmTempOakTN_dict
elif case==3:    
    config_dict=config_US_Ton_dict
elif case==4:    
    config_dict=config_SemiaridGrassland_dict
elif case==5:    
    config_dict=config_MeditPastureCA_dict
elif case==6:
    config_dict=config_SnodgrassTransect_dict
elif case==7:
    config_dict=config_Blodget_dict
elif case==8:
    config_dict=config_Morrow2_dict
elif case==9:
    config_dict=config_Morrow4_dict    
elif case==10:
    config_dict=config_spruces1_dict
elif case==11:
    config_dict=config_sorghum_dict
elif case==12:
    config_dict=config_PLM_dict
write_site_topo_data(config_dict)