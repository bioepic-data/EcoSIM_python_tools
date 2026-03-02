  function CanopyEnergyH2OIter_func(I,J,NZ,FracGrndByPFT,CanopyMassC,TotalSoilPSIMPa_vr,&
    VHeatCapCanopyAir,DIFF,cumPRootH2OUptake,CumPlantHeatLoss2Soil,HeatEvapSens,FDMP,&
    SoilRootResistance_rvr,FracPRoot4Uptake_pvr,AirMicPore4Fill_vr,WatAvail4Uptake_vr,TKCX,CNDT,&
    VHeatCapCanopyPrev_pft,PrecpHeatbyCanopy,PSIGravCanopyHeight,SoiLayerHasRoot_rvr) result(NN)

  implicit none
  integer  , intent(in) :: I, J
  integer  , intent(in) :: NZ
  real(r8) , intent(in) :: FracGrndByPFT,CanopyMassC
  real(r8) , intent(in) :: TotalSoilPSIMPa_vr(JZ1)
  real(r8) , intent(in) :: SoilRootResistance_rvr(jroots,JZ1)
  real(r8) , intent(in) :: FracPRoot4Uptake_pvr(jroots,JZ1,JP1)
  real(r8) , intent(in) :: AirMicPore4Fill_vr(JZ1),WatAvail4Uptake_vr(JZ1)
  real(r8) , intent(in) :: TKCX
  real(r8) , intent(in) :: CNDT
  real(r8) , intent(in) :: VHeatCapCanopyPrev_pft    !canopy heat capacity at previous time step, MJ/K
  real(r8) , intent(in) :: PrecpHeatbyCanopy         !heat added to canopy by precipitation [MJ]
  real(r8) , intent(in) :: PSIGravCanopyHeight       !Graviational water potential at effective canopy height [MPa]
  logical  , intent(in) :: SoiLayerHasRoot_rvr(jroots,JZ1)
  real(r8) , intent(out):: VHeatCapCanopyAir,DIFF
  real(r8) , intent(out):: cumPRootH2OUptake
  real(r8) , intent(out):: CumPlantHeatLoss2Soil  
  real(r8) , intent(out):: HeatEvapSens   !sensible heat due to evaporation/condensation  [MJ]
  real(r8) , intent(out):: FDMP
  real(r8) :: APSILT
  real(r8) :: CCPOLT
  real(r8) :: DTHS1
  real(r8) :: DIFFZ,DIFFU,DPSI
  real(r8) :: EX,PTransPre
  real(r8) :: FTHRM
  real(r8) :: LWRad2Canopy   !long wave radiation (from sky + ground) on canopy [MJ]
  real(r8) :: HeatAdd2Can
  real(r8) :: EffGrndAreaByPFT4H2O,EffGrndAreaByPFT4Heat,PSICanPPre,EvapConductCanopy
  real(r8) :: PSILC               !canopy height adjusted canopy water potential, [MPa]
  real(r8) :: RSSUX,RSSU,RA1,RSSZ
  real(r8) :: TKC1,TKCY
  real(r8) :: cumPRootH2OUptakePre
  real(r8) :: SymplasmicWatPrev,SymplasmicWat  !previous, current biomass-bounded water
  real(r8) :: VPC
  real(r8) :: XC,Stomata_Stress
  real(r8) :: RichardsNO
  integer  :: IC
  logical :: LIterationExit
  real(r8) :: DPSI_old
  character(len=64) :: fmt
!     return variables
  integer :: NN
!     local variables
  integer :: N,L
!     begin_execution

  associate(                                                           &
    AREA3                     => plt_site%AREA3                      , & !input  :soil cross section area (vertical plane defined by its normal direction), [m2]
    OrganOsmoPsi0pt_pft         => plt_ew%OrganOsmoPsi0pt_pft            , & !input  :Organ osmotic potential when canopy water potential = 0 MPa, [MPa]
    CanopyBiomWater_pft       => plt_ew%CanopyBiomWater_pft          , & !input  :canopy water content, [m3 d-2]
    CanopyNonstElmConc_pft    => plt_biom%CanopyNonstElmConc_pft     , & !input  :canopy nonstructural element concentration, [g d-2]
    FracPARads2Canopy_pft     => plt_rad%FracPARads2Canopy_pft       , & !input  :fraction of incoming PAR absorbed by canopy, [-]
    H2OCuticleResist_pft      => plt_photo%H2OCuticleResist_pft      , & !input  :maximum stomatal resistance to vapor, [s h-1]
    LWRadGrnd_col                 => plt_rad%LWRadGrnd_col                   , & !input  :longwave radiation emitted by ground surface, [MJ m-2 h-1]
    LWRadSky_col              => plt_rad%LWRadSky_col                , & !input  :sky longwave radiation , [MJ d-2 h-1]
    MaxSoiL4Root_pft          => plt_morph%MaxSoiL4Root_pft          , & !input  :maximum soil layer number for all root axes,[-]
    MinCanPStomaResistH2O_pft => plt_photo%MinCanPStomaResistH2O_pft , & !input  :canopy minimum stomatal resistance, [s m-1]
    Myco_pft                  => plt_morph%Myco_pft                  , & !input  :mycorrhizal type (no or yes),[-]
    NU                        => plt_site%NU                         , & !input  :current soil surface layer number, [-]
    PSICanopyOsmo_pft         => plt_ew%PSICanopyOsmo_pft            , & !input  :canopy osmotic water potential, [Mpa]
    PSICanopyTurg_pft         => plt_ew%PSICanopyTurg_pft            , & !input  :plant canopy turgor water potential, [MPa]
    PrecIntcptByCanopy_pft    => plt_ew%PrecIntcptByCanopy_pft       , & !input  :water flux into canopy, [m3 d-2 h-1]
    RCS_pft                   => plt_photo%RCS_pft                   , & !input  :shape parameter for calculating stomatal resistance from turgor pressure, [-]
    RIB                       => plt_ew%RIB                          , & !input  :Richardson number for calculating boundary layer resistance, [-]
    RadSWbyCanopy_pft         => plt_rad%RadSWbyCanopy_pft           , & !input  :canopy absorbed shortwave radiation, [MJ d-2 h-1]
    ReistanceCanopy_pft       => plt_ew%ReistanceCanopy_pft          , & !input  :canopy roughness height, [m]
    TKS_vr                    => plt_ew%TKS_vr                       , & !input  :mean annual soil temperature, [K]
    TairK                     => plt_ew%TairK                        , & !input  :air temperature, [K]
    VPA                       => plt_ew%VPA                          , & !input  :vapor concentration, [m3 m-3]
    WatHeldOnCanopy_pft       => plt_ew%WatHeldOnCanopy_pft          , & !input  :canopy surface water content, [m3 d-2]
    ZERO4Groth_pft            => plt_biom%ZERO4Groth_pft             , & !input  :threshold zero for plang growth calculation, [-]
    ZERO4LeafVar_pft          => plt_biom%ZERO4LeafVar_pft           , & !input  :threshold zero for leaf calculation, [-]
    RPlantRootH2OUptk_pvr   => plt_ew%RPlantRootH2OUptk_pvr      , & !inoput :root water uptake, [m2 d-2 h-1]
    CanPStomaResistH2O_pft    => plt_photo%CanPStomaResistH2O_pft    , & !inoput :canopy stomatal resistance, [h m-1]
    CanopyBndlResist_pft      => plt_photo%CanopyBndlResist_pft      , & !inoput :canopy boundary layer resistance, [h m-1]
    EvapTransLHeat_pft        => plt_ew%EvapTransLHeat_pft           , & !inoput :canopy latent heat flux, [MJ d-2 h-1]
    LWRadCanopy_pft           => plt_rad%LWRadCanopy_pft             , & !inoput :canopy longwave radiation, [MJ d-2 h-1]
    PSICanopy_pft             => plt_ew%PSICanopy_pft                , & !inoput :canopy total water potential, [Mpa]
    RadNet2Canopy_pft         => plt_rad%RadNet2Canopy_pft           , & !inoput :canopy net radiation, [MJ d-2 h-1]
    TKC_pft                   => plt_ew%TKC_pft                      , & !inoput :canopy temperature, [K]
    TKCanopy_pft              => plt_ew%TKCanopy_pft                 , & !inoput :canopy temperature, [K]
    Transpiration_pft         => plt_ew%Transpiration_pft            , & !inoput :canopy transpiration, [m2 d-2 h-1]
    VHeatCapCanopy_pft        => plt_ew%VHeatCapCanopy_pft           , & !inoput :canopy heat capacity, [MJ d-2 K-1]
    VapXAir2Canopy_pft        => plt_ew%VapXAir2Canopy_pft           , & !inoput :canopy evaporation, [m2 d-2 h-1]
    DeltaTKC_pft              => plt_ew%DeltaTKC_pft                 , & !output :change in canopy temperature, [K]
    QdewCanopy_pft            => plt_ew%QdewCanopy_pft               , & !output :dew fall on to canopy, [m3 H2O d-2 h-1]
    TdegCCanopy_pft           => plt_ew%TdegCCanopy_pft                & !output :canopy temperature, [oC]
  )
  
  !CCPOLT: total nonstructural canopy C,N,P concentration
  !FTHRM:coefficient for LW emitted by canopy  
  !LWRad2Canopy:long-wave absorbed by canopy
  FTHRM        = EMMC*stefboltz_const*FracPARads2Canopy_pft(NZ)*AREA3(NU)
  LWRad2Canopy = (LWRadSky_col+LWRadGrnd_col)*FracPARads2Canopy_pft(NZ)
  CCPOLT       = CanopyNonstElmConc_pft(ielmc,NZ)+CanopyNonstElmConc_pft(ielmn,NZ) &
    +CanopyNonstElmConc_pft(ielmp,NZ)


  cumPRootH2OUptake     = 0.0_r8
  EffGrndAreaByPFT4H2O  = FracGrndByPFT*AREA3(NU)                    !area coverd by pft m2
  EffGrndAreaByPFT4Heat = FracGrndByPFT*AREA3(NU)*1.25E-03_r8        !1.25e-3 is heat capacity of air [MJ/(m3 K)], assuming air volume is not affected by plant mass
  RA1                   = ReistanceCanopy_pft(NZ)                    !canopy isothermal boundary later resistance

  IC                    = 0
  XC                    = 0.5_r8   !learning/updating rate for canopy temperature, not used now
  LIterationExit        = .false.
  PSICanPPre            = 0.0_r8
  PTransPre             = 0.0_r8
  cumPRootH2OUptakePre  = 0.0_r8
  SymplasmicWatPrev     = 0.0_r8
  DPSI_old              = 0._r8
  CumPlantHeatLoss2Soil = 0._r8

  D4000: DO NN=1,MaxIterNum
!
!     NET RADIATION FROM ABSORBED SW AND NET LW
!
!     LWRadCanopy_pft=LW emitted by canopy
!     DTHS1=net LW absorbed by canopy
!     RadSWbyCanopy_pft=total SW absorbed by canopy
!     RadNet2Canopy_pft=net SW+LW absorbed by canopy
!
    TKC1                  = TKCanopy_pft(NZ)
    LWRadCanopy_pft(NZ)   = FTHRM*TKC1**4._r8              !long wave radiation
    DTHS1                 = LWRad2Canopy-LWRadCanopy_pft(NZ)*2.0_r8        !net long wave radiation to canopy
    RadNet2Canopy_pft(NZ) = RadSWbyCanopy_pft(NZ)+DTHS1  !total radiation to canopy
!
!     BOUNDARY LAYER RESISTANCE FROM RICHARDSON NUMBER
!
!     RI=Ricardson's number
!     RA=canopy boundary layer resistance
!     EvapConductCanopy,VHeatCapCanopyAir=canopy latent,sensible heat conductance
!
    RichardsNO               = RichardsonNumber(RIB,TairK,TKC1)
    CanopyBndlResist_pft(NZ) = AMAX1(MinCanopyBndlResist_pft,0.9_r8*RA1 &
      ,AMIN1(1.1_r8*RA1,ReistanceCanopy_pft(NZ)/(1.0_r8-10.0_r8*RichardsNO)))

    RA1               = CanopyBndlResist_pft(NZ)
    EvapConductCanopy = EffGrndAreaByPFT4H2O/CanopyBndlResist_pft(NZ)  !m2/(h/m)                 = m3/h
    VHeatCapCanopyAir = EffGrndAreaByPFT4Heat/CanopyBndlResist_pft(NZ) !canopy air heat capacity,
!
!     CANOPY WATER AND OSMOTIC POTENTIALS
!
!     OrganOsmoPsi0pt_pft=osmotic potential at PSICanopy_pft=0 from PFT file
!     PSICanopyOsmo_pft,PSICanopyTurg_pft=canopy osmotic,turgor water potential
!
     call update_osmo_turg_pressure(PSICanopy_pft(NZ),CCPOLT,OrganOsmoPsi0pt_pft(NZ),TKC1 &
       ,PSICanopyOsmo_pft(NZ),PSICanopyTurg_pft(NZ),FDMP)
!
!     CANOPY STOMATAL RESISTANCE
!
!     RCS=shape parameter for CanPStomaResistH2O_pftvs PSICanopyTurg_pft from PFT file
!     RC=canopy stomatal resistance
!     MinCanPStomaResistH2O_pft=minimum CanPStomaResistH2O_pftat PSICanopy_pft=0 from stomate.f
!     CuticleResist_pft=cuticular resistance from PFT file
!
    Stomata_Stress             = EXP(RCS_pft(NZ)*PSICanopyTurg_pft(NZ))
    CanPStomaResistH2O_pft(NZ) = MinCanPStomaResistH2O_pft(NZ)+Stomata_Stress &
      *(H2OCuticleResist_pft(NZ)-MinCanPStomaResistH2O_pft(NZ))
!
!     CANOPY VAPOR PRESSURE AND EVAPORATION OF INTERCEPTED WATER
!     OR TRANSPIRATION OF UPTAKEN WATER
!
!     VPC,VPA=vapor pressure inside canopy, in atmosphere
!     TKC1=canopy temperature
!     EX=canopy-atmosphere water flux
!     RA,RZ=canopy boundary layer,surface resistance
!     VapXAir2Canopy_pft=water flux to,from air to canopy surfaces, [ton H2O/(h*m2)]
!     WatHeldOnCanopy_pft=water volume on canopy surfaces
!     EP=water flux to,from inside canopy
!     EvapTransLHeat_pft=canopy latent heat flux
!     HeatEvapSens=convective heat flux from EvapTransLHeat_pft, <0, into air
!     VAP=latent heat of evaporation
!     EvapConductCanopy=aerodynamic conductance

    VPC = vapsat(tkc1)*EXP(18.0_r8*AMAX1(PSICanopy_pft(NZ),-5000._r8)/(RGASC*TKC1))  !ton H2O/m3
    EX  = EvapConductCanopy*(VPA-VPC)   !air to canopy water vap flux, [m/h]*[ton/m3] = [ton H2O/(h*m2)]
    
    !Dew condensation to canopy >0 to canopy
    IF(EX.GT.0.0_r8)THEN     
      VapXAir2Canopy_pft(NZ) = EX*CanopyBndlResist_pft(NZ)/(CanopyBndlResist_pft(NZ)+RZ)
      QdewCanopy_pft(NZ)     = VapXAir2Canopy_pft(NZ)
      EX                     = 0.0_r8
      HeatEvapSens           = VapXAir2Canopy_pft(NZ)*cpw*TairK               !enthalpy of condensed water add to canopy, MJ/(h)
    !canopy lose water, and there is canopy-held water  
    ELSEIF(EX.LE.0.0_r8)THEN 
      if(WatHeldOnCanopy_pft(NZ).GT.0.0_r8)THEN
        !evaporation, and there is water stored in canopy
        !VapXAir2Canopy_pft <0._r8, off canopy as evaporation, cannot be more than WatHeldOnCanopy_pft(NZ)
        VapXAir2Canopy_pft(NZ) = AMAX1(EX*CanopyBndlResist_pft(NZ)/(CanopyBndlResist_pft(NZ)+RZ),-WatHeldOnCanopy_pft(NZ))
        EX                     = EX-VapXAir2Canopy_pft(NZ)                !demand for transpiration
        HeatEvapSens           = VapXAir2Canopy_pft(NZ)*cpw*TKC1          !enthalpy of evaporated water leaving canopy
      ELSE
        VapXAir2Canopy_pft(NZ) =0._r8
        HeatEvapSens = 0._r8  
      ENDIF
    ENDIF

    !Transpiration_pft<0 means canopy lose water through transpiration
    !EvapTransLHeat_pft:latent heat flux, negative means into atmosphere

    Transpiration_pft(NZ)  = EX*CanopyBndlResist_pft(NZ)/(CanopyBndlResist_pft(NZ)+CanPStomaResistH2O_pft(NZ))
    EvapTransLHeat_pft(NZ) = (Transpiration_pft(NZ)+VapXAir2Canopy_pft(NZ))*EvapLHTC
    HeatEvapSens           = HeatEvapSens + Transpiration_pft(NZ)*cpw*TKC1
!
!     SENSIBLE + STORAGE HEAT FROM RN, LE AND CONVECTIVE HEAT FLUXES
!
!     HeatSenAddStore=initial estimate of sensible+storage heat flux
!     PrecpHeatbyCanopy=convective heat flux from precip to canopy
!
    HeatAdd2Can=RadNet2Canopy_pft(NZ)+EvapTransLHeat_pft(NZ)+HeatEvapSens+PrecpHeatbyCanopy-CumPlantHeatLoss2Soil
!
!     SOLVE FOR CANOPY TEMPERATURE CAUSED BY SENSIBLE + STORAGE HEAT
!
!     VHeatCapCanopy_pft=canopy heat capacity
!     TKCY=equilibrium canopy temperature for HeatSenAddStore
!
!   VHeatCapCanopyPrev_pft= canopy heat capacity, including biomass, held and bounded water
!   assuming transpiration does not change water binded by the canopy, i.e. CanopyBiomWater_pft(NZ)
!   canopy bound water is changing
    VHeatCapCanopy_pft(NZ)=VHeatCapCanopyPrev_pft+cpw*(PrecIntcptByCanopy_pft(NZ)+VapXAir2Canopy_pft(NZ) &
       +Transpiration_pft(NZ)-cumPRootH2OUptake)
!   new canopy temperature 
    TKCY=(TKCX*VHeatCapCanopyPrev_pft+HeatAdd2Can+TairK*VHeatCapCanopyAir)/(VHeatCapCanopy_pft(NZ)+VHeatCapCanopyAir)

    !limit canopy temperature to no different from air for more than 10 K
    TKCY=AMIN1(TairK+10.0_r8,AMAX1(TairK-10.0_r8,TKCY))
!
!     RESET CANOPY TEMPERATURE FOR NEXT ITERATION
!
!     XC,IC=magnitude,direction of change in canopy temp for next cycle
!
    IF((IC.EQ.0 .AND. TKCY.GT.TKC1) .OR. (IC.EQ.1 .AND. TKCY.LT.TKC1))THEN
      XC=0.5_r8*XC
    ENDIF
    !0.1 is the learning/updating rate
    TKCanopy_pft(NZ)=TKC1+0.1_r8*(TKCY-TKC1)

    IF(TKCY.GT.TKC1)THEN
      !warming
      IC=1
    ELSE
      !cooling or no change
      IC=0
    ENDIF

!
!     IF CONVERGENCE CRITERION IS MET OR ON EVERY TENTH ITERATION,
!     PROCEED TO WATER BALANCE
!
!
    IF(ABS(TKCY-TKC1).LT.0.05_r8 .OR. (NN/10)*10.EQ.NN)THEN
      cumPRootH2OUptake = 0.0_r8
      PSILC             = PSICanopy_pft(NZ)+PSIGravCanopyHeight
!
!     ROOT WATER UPTAKE FROM SOIL-CANOPY WATER POTENTIALS,
!     SOIL + ROOT HYDRAULIC RESISTANCES
!
!     SoiLayerHasRoot_rvr=rooted layer flag
!     RPlantRootH2OUptk_pvr=root water uptake from soil layer > 0
!     WatAvail4Uptake_vr,AirMicPore4Fill_vr=water volume available for uptake,air volume
!     FracPRoot4Uptake_pvr=PFT fraction of biome root mass
!     PSILC=height corrected canopy water potential 
!     SoilRootResistance_rvr=total soil+root resistance
!     cumPRootH2OUptake=total root water uptake from soil 
!     CumPlantHeatLoss2Soil (<0.), add heat to canopy 

      CumPlantHeatLoss2Soil=0._r8
      D4200: DO N=1,Myco_pft(NZ)
        D4201: DO L=NU,MaxSoiL4Root_pft(NZ)
          IF(SoiLayerHasRoot_rvr(N,L))THEN
            !<0 active uptake
            RPlantRootH2OUptk_pvr(N,L,NZ)=AMAX1(AZMIN1(-WatAvail4Uptake_vr(L)*FracPRoot4Uptake_pvr(N,L,NZ)), &
              AMIN1((PSILC-TotalSoilPSIMPa_vr(L))/SoilRootResistance_rvr(N,L), &
              AirMicPore4Fill_vr(L)*FracPRoot4Uptake_pvr(N,L,NZ)))

            !plant/myco lose water to soil > 0
            IF(RPlantRootH2OUptk_pvr(N,L,NZ).GT.0.0_r8)THEN              
              !why multiply 0.1 here? I don't know
              RPlantRootH2OUptk_pvr(N,L,NZ)=0.1_r8*RPlantRootH2OUptk_pvr(N,L,NZ)

              !plant moves heat from canopy to soil,
              CumPlantHeatLoss2Soil=CumPlantHeatLoss2Soil+cpw*RPlantRootH2OUptk_pvr(N,L,NZ)*TKC1

            !plant/myco gains water from soil < 0
            else  
              CumPlantHeatLoss2Soil=CumPlantHeatLoss2Soil+cpw*RPlantRootH2OUptk_pvr(N,L,NZ)*TKS_vr(L)
            ENDIF
            cumPRootH2OUptake=cumPRootH2OUptake+RPlantRootH2OUptk_pvr(N,L,NZ)
          ELSE
            RPlantRootH2OUptk_pvr(N,L,NZ)=0.0_r8
          ENDIF
        enddo D4201
      ENDDO D4200
      !turn it off at the moment
!
!     TEST TRANSPIRATION - ROOT WATER UPTAKE VS. CHANGE IN CANOPY
!     WATER STORAGE
!
!     SymplasmicWat  = total water can be held in biomass
!     CanopyBiomWater_pft= canopy water content held in biomass
!     DIFFZ= extra canopy water binding capacity
!     DIFFU= change to canopy binded water
!     DIFFU-DIFFZ=residual of canopy binded water,
!     >0 gain binded water (increase leaf P, more positive), <0 lose binded water (more uptake, decrease leaf water P) 
!     DIFF=normalized difference between DIFFZ and DIFFU
!     5.0E-03=acceptance criterion for DIFF
!     RSSZ=change in canopy water potl vs change in canopy water cnt
!     RSSU=change in canopy water potl vs change in transpiration
      
      SymplasmicWat = ppmc*CanopyMassC/FDMP              
      DIFFZ         = SymplasmicWat-CanopyBiomWater_pft(NZ)    !biomass water deficit
      DIFFU         = Transpiration_pft(NZ)-cumPRootH2OUptake  !root water uptake excess

      !ideally, the difference between DIFFZ and DIFFU should be as small as possible      
      IF(.not.isclose(cumPRootH2OUptake,0.0_r8))THEN
        DIFF=ABS((DIFFU-DIFFZ)/cumPRootH2OUptake)
      ELSE
        DIFF=ABS(DIFFU-DIFFZ)/SymplasmicWat
      ENDIF

      !the relative difference is small enough
      IF(DIFF.LT.5.0E-03_r8)THEN
        IF(LIterationExit)EXIT
        LIterationExit=.true.
        CALL StomatalDynamics(I,J,NZ)
        CYCLE
      ENDIF
      
      IF(ABS(SymplasmicWat-SymplasmicWatPrev).GT.ZERO4Groth_pft(NZ))THEN
        RSSZ=ABS((PSICanopy_pft(NZ)-PSICanPPre)/(SymplasmicWat-SymplasmicWatPrev))
      ELSEIF(CNDT.GT.ZERO4Groth_pft(NZ))THEN
        RSSZ=1.0_r8/CNDT   !resistance
      ELSE
        RSSZ=ZERO4LeafVar_pft(NZ)
      ENDIF
      
      IF(ABS(Transpiration_pft(NZ)-PTransPre).GT.ZERO4Groth_pft(NZ))THEN
        RSSUX=ABS((PSICanopy_pft(NZ)-PSICanPPre)/(Transpiration_pft(NZ)-PTransPre))
        IF(CNDT.GT.ZERO4Groth_pft(NZ))THEN
          RSSU=AMIN1(1.0_r8/CNDT,RSSUX)  !resistance for uptake
        ELSE
          RSSU=RSSUX
        ENDIF
      ELSEIF(ABS(cumPRootH2OUptake-cumPRootH2OUptakePre).GT.ZERO4Groth_pft(NZ))THEN
        RSSUX=ABS((PSICanopy_pft(NZ)-PSICanPPre)/(cumPRootH2OUptake-cumPRootH2OUptakePre))
        IF(CNDT.GT.ZERO4Groth_pft(NZ))THEN
          RSSU=AMIN1(1.0_r8/CNDT,RSSUX)  !resistance
        ELSE
          RSSU=RSSUX
        ENDIF
      ELSEIF(CNDT.GT.ZERO4Groth_pft(NZ))THEN
        RSSU=1.0_r8/CNDT
      ELSE
        RSSU=ZERO4LeafVar_pft(NZ)
      ENDIF
!
!     CHANGE IN CANOPY WATER POTENTIAL REQUIRED TO BRING AGREEMENT
!     BETWEEN TRANSPIRATION - ROOT WATER UPTAKE AND CHANGE IN CANOPY
!     WATER STORAGE
!
!     DPSI=change in PSICanopy_pft(for next convergence cycle
!     1.0E-03=acceptance criterion for DPSI
!
      DPSI=AMIN1(AMIN1(RSSZ,RSSU)*(DIFFU-DIFFZ),ABS(PSICanopy_pft(NZ)))

!     IF CONVERGENCE CRITERION IS MET THEN FINISH,
!     OTHERWISE START NEXT ITERATION WITH CANOPY WATER POTENTIAL
!     TRANSPIRATION, UPTAKE AND WATER CONTENT FROM CURRENT ITERATION
!
      IF((NN.GE.30 .AND. ABS(DPSI).LT.1.0E-03_r8) .OR. NN.GE.MaxIterNum)then
        IF(LIterationExit)EXIT
        LIterationExit=.true.
        CALL StomatalDynamics(I,J,NZ)      
      ELSE
        !prepare for next iteration
        PSICanPPre           = PSICanopy_pft(NZ)
        PTransPre            = Transpiration_pft(NZ)
        cumPRootH2OUptakePre = cumPRootH2OUptake
        SymplasmicWatPrev    = SymplasmicWat

        PSICanopy_pft(NZ) = AZMIN1(PSICanopy_pft(NZ)+0.1_r8*DPSI)
        DPSI_old          = DPSI
        XC                = 0.50_r8!
      ENDIF
    ENDIF
  ENDDO D4000

!
!     FINAL CANOPY TEMPERATURE, DIFFERENCE WITH AIR TEMPERATURE
!
!     TKC=final estimate of canopy temperature TKCanopy_pft
!     TairK=current air temperature
!     DeltaTKC_pft=TKC-TairK for next hour
!
  TKC_pft(NZ)         = TKCanopy_pft(NZ)
  TdegCCanopy_pft(NZ) = units%Kelvin2Celcius(TKC_pft(NZ))
  DeltaTKC_pft(NZ)    = TKC_pft(NZ)-TairK

  end associate
  end function CanopyEnergyH2OIter_func