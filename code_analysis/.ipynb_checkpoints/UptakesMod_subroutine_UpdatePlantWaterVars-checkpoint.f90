  subroutine UpdatePlantWaterVars(NZ,VHeatCapCanopyAir,TotalSoilPSIMPa_vr,RootResist_rvr,SoiH2OResist,SoilRootResistance_rvr,&
    TKCX,VHeatCapCanopyPrev_pft,PrecpHeatbyCanopy,cumPRootH2OUptake,CumPlantHeatLoss2Soil,HeatEvapSens,SoiLayerHasRoot_rvr)
  !
  !Description
  !Update canopy heat and water states after the numerical iterations.
  implicit none
  integer, intent(in) :: NZ
  real(r8), intent(in) :: VHeatCapCanopyAir
  real(r8), intent(in) :: TotalSoilPSIMPa_vr(JZ1)    !Elevation adjusted soil water potential [MPa]
  real(r8), intent(in) :: RootResist_rvr(jroots,JZ1)
  real(r8), intent(in) :: SoiH2OResist(jroots,JZ1)
  real(r8), intent(in) :: SoilRootResistance_rvr(jroots,JZ1)
  real(r8), intent(in) :: TKCX,VHeatCapCanopyPrev_pft
  real(r8), intent(in) :: PrecpHeatbyCanopy
  real(r8), intent(in) :: cumPRootH2OUptake
  real(r8), intent(in) :: HeatEvapSens                     !sensible heat associated with evaporation [MJ/h]
  real(r8), intent(in) :: CumPlantHeatLoss2Soil
  logical , intent(in) :: SoiLayerHasRoot_rvr(jroots,JZ1)  !indicator of root prescence

  character(len=*), parameter :: subname='UpdatePlantWaterVars'
  real(r8) :: CCPOLT,CanopyMassC
  real(r8) :: OSWT
  integer :: N,L
  associate(                                                          &
    OrganOsmoPsi0pt_pft         => plt_ew%OrganOsmoPsi0pt_pft           , & !input  :Organ osmotic potential when canopy water potential = 0 MPa, [MPa]
    CanopyLeafSheathC_pft      => plt_biom%CanopyLeafSheathC_pft      , & !input  :canopy leaf + sheath C, [g d-2]
    CanopySapwoodC_pft          => plt_biom%CanopySapwoodC_pft          , & !input  :canopy active stalk C, [g d-2]
    MaxSoiL4Root_pft          => plt_morph%MaxSoiL4Root_pft         , & !input  :maximum soil layer number for all root axes,[-]
    Myco_pft                  => plt_morph%Myco_pft                 , & !input  :mycorrhizal type (no or yes),[-]
    NU                        => plt_site%NU                        , & !input  :current soil surface layer number, [-]
    PSICanopy_pft             => plt_ew%PSICanopy_pft               , & !input  :canopy total water potential, [Mpa]
    PSIRootOSMO_vr            => plt_ew%PSIRootOSMO_vr              , & !input  :root osmotic water potential, [Mpa]
    PSIRootTurg_vr            => plt_ew%PSIRootTurg_vr              , & !input  :root turgor water potential, [Mpa]
    PrecIntcptByCanopy_pft    => plt_ew%PrecIntcptByCanopy_pft      , & !input  :water flux into canopy, [m3 d-2 h-1]
    RootNonstructElmConc_rpvr => plt_biom%RootNonstructElmConc_rpvr , & !input  :root layer nonstructural C concentration, [g g-1]
    TKCanopy_pft              => plt_ew%TKCanopy_pft                , & !input  :canopy temperature, [K]
    TKS_vr                    => plt_ew%TKS_vr                      , & !input  :mean annual soil temperature, [K]
    TairK                     => plt_ew%TairK                       , & !input  :air temperature, [K]
    Transpiration_pft         => plt_ew%Transpiration_pft           , & !input  :canopy transpiration, [m2 d-2 h-1]
    VapXAir2Canopy_pft        => plt_ew%VapXAir2Canopy_pft          , & !input  :canopy evaporation, [m2 d-2 h-1]
    CanopyBiomWater_pft       => plt_ew%CanopyBiomWater_pft         , & !inoput :canopy water content, [m3 d-2]
    PSIRoot_pvr               => plt_ew%PSIRoot_pvr                 , & !inoput :root total water potential, [Mpa]
    VHeatCapCanopy_pft        => plt_ew%VHeatCapCanopy_pft          , & !inoput :canopy heat capacity, [MJ d-2 K-1]
    WatHeldOnCanopy_pft       => plt_ew%WatHeldOnCanopy_pft         , & !inoput :canopy surface water content, [m3 d-2]
    HeatStorCanopy_pft        => plt_ew%HeatStorCanopy_pft          , & !output :canopy storage heat flux, [MJ d-2 h-1]
    HeatXAir2PCan_pft         => plt_ew%HeatXAir2PCan_pft             & !output :canopy sensible heat flux, [MJ d-2 h-1]
  )
  !
  !     CANOPY SURFACE WATER STORAGE, SENSIBLE AND STORAGE HEAT FLUXES
  !     (NOT EXPLICITLY CALCULATED IN CONVERGENCE SOLUTION)
  !
  !     VOLWP,WatHeldOnCanopy_pft=water volume in canopy,on canopy surfaces
  !     HeatXAir2PCan_pft=canopy sensible,storage heat fluxes
  !     HeatStorCanopy_pft=Radiation-latent heat-sens, i.e. (>0) residual heat from air to canopy
  !     VHeatCapCanopyPrev_pft,VHeatCapCanopy_pft=previous,current canopy heat capacity
  !     VHeatCapCanopyAir=canopy sensible heat conductance
  !     HeatEvapSens=convective heat flux from latent heat flux (>0)
  !     PrecpHeatbyCanopy=convective heat flux from precip to canopy
  !     cumPRootH2OUptake < 0., add water to canopy 
  !     Transpiration_pft < 0., lost from canopy
  CanopyBiomWater_pft(NZ) = CanopyBiomWater_pft(NZ)+Transpiration_pft(NZ)-cumPRootH2OUptake
  CanopyMassC             = AZMAX1(CanopyLeafSheathC_pft(NZ)+CanopySapwoodC_pft(NZ))
  WatHeldOnCanopy_pft(NZ) = WatHeldOnCanopy_pft(NZ)+PrecIntcptByCanopy_pft(NZ)+VapXAir2Canopy_pft(NZ)
  VHeatCapCanopy_pft(NZ)  = cpw*(CanopyMassC*SpecStalkVolume+WatHeldOnCanopy_pft(NZ)+CanopyBiomWater_pft(NZ))
  HeatXAir2PCan_pft(NZ)   = VHeatCapCanopyAir*(TairK-TKCanopy_pft(NZ))
  HeatStorCanopy_pft(NZ)  = TKCX*VHeatCapCanopyPrev_pft-TKCanopy_pft(NZ)*VHeatCapCanopy_pft(NZ)+HeatEvapSens+PrecpHeatbyCanopy
  !
  !     ROOT TOTAL, OSMOTIC AND TURGOR WATER POTENTIALS
  !
  !     PSIRoot_pvr,PSICanopy_pft=root,canopy total water potential
  !     TotalSoilPSIMPa_vr=total soil water potential PSIST adjusted for surf elevn
  !     SoiH2OResist,SoilRootResistance_rvr,RootResist=soil,soil+root,root radial+axial resistance
  !     PSIRootOSMO_vr,PSIRootTurg_vr=root osmotic,turgor water potential
  !     OrganOsmoPsi0pt_pft=osmotic potential at PSIRoot_pvr=0 from PFT file

  !compute root pressure assuming zero water storage capacity in root, cf. Eq. (36) Grant (1998), Ecological modelling.
  D4505: DO N=1,Myco_pft(NZ)
    D4510: DO L=NU,MaxSoiL4Root_pft(NZ)
      IF(SoiLayerHasRoot_rvr(N,L))THEN
        PSIRoot_pvr(N,L,NZ)=AZMIN1((TotalSoilPSIMPa_vr(L)*RootResist_rvr(N,L) &
          +PSICanopy_pft(NZ)*SoiH2OResist(N,L))/SoilRootResistance_rvr(N,L))
      ELSE
        PSIRoot_pvr(N,L,NZ)=TotalSoilPSIMPa_vr(L)
      ENDIF           
      !obtain total reserve
      CCPOLT=sum(RootNonstructElmConc_rpvr(1:NumPlantChemElms,N,L,NZ))

      CALL update_osmo_turg_pressure(PSIRoot_pvr(N,L,NZ),CCPOLT,OrganOsmoPsi0pt_pft(NZ),TKS_vr(L),&
        PSIRootOSMO_vr(N,L,NZ),PSIRootTurg_vr(N,L,NZ))

    ENDDO D4510
  ENDDO D4505
  call PrintInfo('end '//subname)
  end associate
  end subroutine UpdatePlantWaterVars