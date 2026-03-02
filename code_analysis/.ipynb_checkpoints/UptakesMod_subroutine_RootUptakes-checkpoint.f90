  subroutine RootUptakes(I,J)
!  
!  Description: MAIN_CALL
!
!     THIS subroutine CALCULATES EXCHANGES OF ENERGY, C, N AND P
!     BETWEEN THE CANOPY AND THE ATMOSPHERE AND BETWEEN ROOTS AND THE SOIL
!
  implicit none
  integer, intent(in) :: I, J
  
  character(len=*), parameter :: subname='RootUptakes'
  integer :: NN,N,NZ,K,L
  real(r8) :: FracGrndByPFT
  real(r8) :: VHeatCapCanopyAir
  real(r8) :: CanopyMassC                !Canopy C mass, g/m2
  real(r8) :: TotalSoilPSIMPa_vr(JZ1)    !total soil matric pressure, removing elevation adjustment [MPa]
  real(r8) :: PathLen_pvr(jroots,JZ1)
  real(r8) :: FineRootRadius_rvr(jroots,JZ1)
  real(r8) :: RootResist_rvr(jroots,JZ1)
  real(r8) :: RootResistSoi_rvr(jroots,JZ1)
  real(r8) :: RootResistPrimary(jroots,JZ1)
  real(r8) :: RootResist2ndary(jroots,JZ1)
  real(r8) :: SoiH2OResist(jroots,JZ1)
  real(r8) :: SoilRootResistance_rvr(jroots,JZ1),AllRootC_vr(JZ1)
  real(r8) :: FracPRoot4Uptake_pvr(jroots,JZ1,JP1)
  real(r8) :: FracMinRoot4Uptake_rpvr(jroots,JZ1,JP1)
  real(r8) :: FracSoilLBy1stRoots_pvr(JZ1,JP1)
  real(r8) :: RootEffLen4Absorption_pvr(jroots,JZ1)
  real(r8) :: AirMicPore4Fill_vr(JZ1)  !
  real(r8) :: WatAvail4Uptake_vr(JZ1)
  real(r8) :: TKCX,CNDT,PrecpHeatbyCanopy
  real(r8) :: VHeatCapCanopyPrev_pft  !canopy heat capacity, J/K
  real(r8) :: DIFF
  real(r8) :: PSIGravCanopyHeight               !gravitation potential at effective canopy height [MPa]
  real(r8) :: cumPRootH2OUptake,HeatEvapSens
  real(r8) :: CumPlantHeatLoss2Soil
  real(r8) :: FDMP
  logical  :: HydroActivePlant
  logical  :: SoiLayerHasRoot_rvr(jroots,JZ1)
!     begin_execution
  associate(                                                        &
    AREA3                     => plt_site%AREA3                   , & !input  :soil cross section area (vertical plane defined by its normal direction), [m2]
    CanopyBiomWater_pft       => plt_ew%CanopyBiomWater_pft       , & !input  :canopy water content, [m3 d-2]
    CanopyBndlResist_pft      => plt_photo%CanopyBndlResist_pft   , & !input  :canopy boundary layer resistance, [h m-1]
    CanopyLeafArea_col        => plt_morph%CanopyLeafArea_col     , & !input  :grid canopy leaf area, [m2 d-2]
    CanopyLeafSheathC_pft      => plt_biom%CanopyLeafSheathC_pft    , & !input  :canopy leaf + sheath C, [g d-2]
    CanopySapwoodC_pft          => plt_biom%CanopySapwoodC_pft        , & !input  :canopy active stalk C, [g d-2]
    CumSoilThickness_vr       => plt_site%CumSoilThickness_vr     , & !input  :depth to bottom of soil layer from surface of grid cell, [m]
    EvapTransLHeat_pft        => plt_ew%EvapTransLHeat_pft        , & !input  :canopy latent heat flux, [MJ d-2 h-1]
    FracPARads2Canopy_pft     => plt_rad%FracPARads2Canopy_pft    , & !input  :fraction of incoming PAR absorbed by canopy, [-]
    HeatXAir2PCan_pft         => plt_ew%HeatXAir2PCan_pft         , & !input  :canopy sensible heat flux, [MJ d-2 h-1]
    IsPlantActive_pft         => plt_pheno%IsPlantActive_pft      , & !input  :flag for living pft, [-]
    LeafStalkArea_col         => plt_morph%LeafStalkArea_col      , & !input  :stalk area of combined, each PFT canopy,[m^2 d-2]
    LeafStalkArea_pft         => plt_morph%LeafStalkArea_pft      , & !input  :plant leaf+stem/stalk area, [m2 d-2]
    MainBranchNum_pft         => plt_morph%MainBranchNum_pft      , & !input  :number of main branch,[-]
    NP                        => plt_site%NP                      , & !input  :current number of plant species,[-]
    NU                        => plt_site%NU                      , & !input  :current soil surface layer number, [-]
    PlantPopu_col             => plt_site%PlantPopu_col           , & !input  :total plant population, [plants d-2]
    PlantPopulation_pft       => plt_site%PlantPopulation_pft     , & !input  :plant population, [d-2]
    PrecIntcptByCanopy_pft    => plt_ew%PrecIntcptByCanopy_pft    , & !input  :water flux into canopy, [m3 d-2 h-1]
    Root1stDepz_raxes           => plt_morph%Root1stDepz_raxes        , & !input  :root layer depth, [m]
    SeedDepth_pft             => plt_morph%SeedDepth_pft          , & !input  :seeding depth, [m]
    TKC_pft                   => plt_ew%TKC_pft                   , & !input  :canopy temperature, [K]
    TairK                     => plt_ew%TairK                     , & !input  :air temperature, [K]
    WatHeldOnCanopy_pft       => plt_ew%WatHeldOnCanopy_pft       , & !input  :canopy surface water content, [m3 d-2]
    ZERO4LeafVar_pft          => plt_biom%ZERO4LeafVar_pft        , & !input  :threshold zero for leaf calculation, [-]
    ZEROS                     => plt_site%ZEROS                   , & !input  :threshold zero for numerical stability,[-]
    iPlantCalendar_brch       => plt_pheno%iPlantCalendar_brch    , & !input  :plant growth stage, [-]
    Air_Heat_Latent_store_col => plt_ew%Air_Heat_Latent_store_col , & !inoput :total latent heat flux x boundary layer resistance, [MJ m-1]
    Air_Heat_Sens_store_col   => plt_ew%Air_Heat_Sens_store_col   , & !inoput :total sensible heat flux x boundary layer resistance, [MJ m-1]
    PSICanopy_pft             => plt_ew%PSICanopy_pft             , & !inoput :canopy total water potential, [Mpa]
    Transpiration_pft         => plt_ew%Transpiration_pft         , & !output :canopy transpiration, [m2 d-2 h-1]
    VapXAir2Canopy_pft        => plt_ew%VapXAir2Canopy_pft          & !output :canopy evaporation, [m2 d-2 h-1]
  )

  call PrintInfo('beg '//subname)

  call PrepH2ONutrientUptake(TotalSoilPSIMPa_vr,AllRootC_vr,AirMicPore4Fill_vr,WatAvail4Uptake_vr)
!
!     IF PLANT SPECIES EXISTS

  DO NZ=1,NP

    IF(IsPlantActive_pft(NZ).EQ.iActive .AND. PlantPopulation_pft(NZ).GT.0.0_r8)THEN
      
      call UpdateCanopyProperty(NZ)

!     STOMATE=solve for minimum canopy stomatal resistance
      
      CALL StomatalDynamics(I,J,NZ)
!
      if(lverb)write(*,*)'CALCULATE VARIABLES USED IN ROOT UPTAKE OF WATER AND NUTRIENTS'
      call UpdateRootProperty(NZ,PathLen_pvr,FineRootRadius_rvr,AllRootC_vr,FracPRoot4Uptake_pvr,&
        FracMinRoot4Uptake_rpvr,FracSoilLBy1stRoots_pvr,RootEffLen4Absorption_pvr)
!
!     CALCULATE CANOPY WATER STATUS FROM CONVERGENCE SOLUTION FOR
!     TRANSPIRATION - ROOT WATER UPTAKE = CHANGE IN CANOPY WATER CONTENT
!
      CanopyMassC            = AZMAX1(CanopyLeafSheathC_pft(NZ)+CanopySapwoodC_pft(NZ))
      VHeatCapCanopyPrev_pft = cpw*(CanopyMassC*SpecStalkVolume+WatHeldOnCanopy_pft(NZ)+CanopyBiomWater_pft(NZ))

      HydroActivePlant=(iPlantCalendar_brch(ipltcal_Emerge,MainBranchNum_pft(NZ),NZ).NE.0)             &  !plant emerged
        .AND.(LeafStalkArea_pft(NZ).GT.ZERO4LeafVar_pft(NZ).AND.FracPARads2Canopy_pft(NZ).GT.0.0_r8)   &  !active canopy
        .AND.(Root1stDepz_raxes(ipltroot,1,NZ).GT.SeedDepth_pft(NZ)+CumSoilThickness_vr(0))              &  !active root
        .and. CanopyMassC>0._r8

      IF(HydroActivePlant)THEN  
!
        call CalcResistance(NZ,PathLen_pvr,FineRootRadius_rvr,RootEffLen4Absorption_pvr,RootResist_rvr,RootResistSoi_rvr,&
          RootResistPrimary,RootResist2ndary,SoiH2OResist,SoilRootResistance_rvr,CNDT,PSIGravCanopyHeight,SoiLayerHasRoot_rvr)
!
!       INITIALIZE CANOPY WATER POTENTIAL, OTHER VARIABLES USED IN ENERGY
!       BALANCE THAT DON'T NEED TO BE RECALCULATED DURING CONVERGENCE
!
        PSICanopy_pft(NZ)      = AMIN1(-ppmc,0.667_r8*PSICanopy_pft(NZ))
        Transpiration_pft(NZ)  = 0.0_r8
        VapXAir2Canopy_pft(NZ) = 0.0_r8
        PrecpHeatbyCanopy      = PrecIntcptByCanopy_pft(NZ)*cpw*TairK

        IF(LeafStalkArea_col.GT.ZEROS)THEN
          !the grid has significant canopy (leaf+steam) area
          FracGrndByPFT=LeafStalkArea_pft(NZ)/LeafStalkArea_col*AMIN1(1.0_r8,0.5_r8*CanopyLeafArea_col/AREA3(NU))
        ELSEIF(PlantPopu_col.GT.ZEROS)THEN
          !total population is > 0
          FracGrndByPFT=PlantPopulation_pft(NZ)/PlantPopu_col
        ELSE
          FracGrndByPFT=1.0_r8/NP
        ENDIF

        TKCX   = TKC_pft(NZ)
!
!     CONVERGENCE SOLUTION
!
        NN=CanopyEnergyH2OIter_func(I,J,NZ,FracGrndByPFT,CanopyMassC,&
          TotalSoilPSIMPa_vr,VHeatCapCanopyAir,DIFF,cumPRootH2OUptake,CumPlantHeatLoss2Soil,&
          HeatEvapSens,FDMP,SoilRootResistance_rvr,FracPRoot4Uptake_pvr,AirMicPore4Fill_vr,&
          WatAvail4Uptake_vr,TKCX,CNDT,VHeatCapCanopyPrev_pft,PrecpHeatbyCanopy,PSIGravCanopyHeight,SoiLayerHasRoot_rvr)
!
!     IF CONVERGENCE NOT ACHIEVED (RARE), SET DEFAULT
!     TEMPERATURES, ENERGY FLUXES, WATER POTENTIALS, RESISTANCES
!
        call HandlingDivergence(I,J,NN,NZ,TotalSoilPSIMPa_vr,DIFF,FDMP)

        call UpdatePlantWaterVars(NZ,VHeatCapCanopyAir,TotalSoilPSIMPa_vr,RootResist_rvr,SoiH2OResist,SoilRootResistance_rvr,&
          TKCX,VHeatCapCanopyPrev_pft,PrecpHeatbyCanopy,cumPRootH2OUptake,CumPlantHeatLoss2Soil,HeatEvapSens,SoiLayerHasRoot_rvr)
!
!     DEFAULT VALUES IF PLANT SPECIES DOES NOT EXIST
!
      ELSE
        call HandleBareSoil(NZ,TotalSoilPSIMPa_vr,FDMP)
      ENDIF

      Air_Heat_Latent_store_col = Air_Heat_Latent_store_col+EvapTransLHeat_pft(NZ)*CanopyBndlResist_pft(NZ)
      Air_Heat_Sens_store_col   = Air_Heat_Sens_store_col+HeatXAir2PCan_pft(NZ)*CanopyBndlResist_pft(NZ)

      if(.not.ldo_sp_mode) then      
        call SetCanopyGrowthFuncs(I,J,NZ)
    
        call PlantNutientO2Uptake(I,J,NZ,FDMP,PathLen_pvr,FineRootRadius_rvr,FracPRoot4Uptake_pvr,&
          FracMinRoot4Uptake_rpvr,FracSoilLBy1stRoots_pvr,RootEffLen4Absorption_pvr)
      endif    
    ENDIF
  ENDDO

  call PrintInfo('end '//subname)
  RETURN
  end associate
  END subroutine RootUptakes