  subroutine HandleBareSoil(NZ,TotalSoilPSIMPa_vr,FDMP)
  !
  !plant has not emerged yet
  use data_const_mod, only : spval => DAT_CONST_SPVAL
  implicit none
  integer, intent(in) :: NZ
  real(r8), intent(in) :: TotalSoilPSIMPa_vr(JZ1)
  real(r8), intent(out):: FDMP
  integer :: N,L
  real(r8) :: APSILT
  real(r8) :: CCPOLT
  real(r8) :: FTHRM
  real(r8) :: OSWT,Stomata_Stress

! begin_execution
  associate(                                                           &
    AREA3                     => plt_site%AREA3                      , & !input  :soil cross section area (vertical plane defined by its normal direction), [m2]
    OrganOsmoPsi0pt_pft         => plt_ew%OrganOsmoPsi0pt_pft            , & !input  :Organ osmotic potential when canopy water potential = 0 MPa, [MPa]
    CanopyHeight_pft          => plt_morph%CanopyHeight_pft          , & !input  :canopy height, [m]
    CanopyNonstElmConc_pft    => plt_biom%CanopyNonstElmConc_pft     , & !input  :canopy nonstructural element concentration, [g d-2]
    FracPARads2Canopy_pft     => plt_rad%FracPARads2Canopy_pft       , & !input  :fraction of incoming PAR absorbed by canopy, [-]
    H2OCuticleResist_pft      => plt_photo%H2OCuticleResist_pft      , & !input  :maximum stomatal resistance to vapor, [s h-1]
    MaxSoiL4Root_pft          => plt_morph%MaxSoiL4Root_pft          , & !input  :maximum soil layer number for all root axes,[-]
    MinCanPStomaResistH2O_pft => plt_photo%MinCanPStomaResistH2O_pft , & !input  :canopy minimum stomatal resistance, [s m-1]
    Myco_pft                  => plt_morph%Myco_pft                  , & !input  :mycorrhizal type (no or yes),[-]
    NGTopRootLayer_pft        => plt_morph%NGTopRootLayer_pft        , & !input  :soil layer at planting depth, [-]
    NU                        => plt_site%NU                         , & !input  :current soil surface layer number, [-]
    PSICanopyOsmo_pft         => plt_ew%PSICanopyOsmo_pft            , & !input  :canopy osmotic water potential, [Mpa]
    PSICanopyTurg_pft         => plt_ew%PSICanopyTurg_pft            , & !input  :plant canopy turgor water potential, [MPa]
    PSIRootOSMO_vr            => plt_ew%PSIRootOSMO_vr               , & !input  :root osmotic water potential, [Mpa]
    PSIRootTurg_vr            => plt_ew%PSIRootTurg_vr               , & !input  :root turgor water potential, [Mpa]
    RCS_pft                   => plt_photo%RCS_pft                   , & !input  :shape parameter for calculating stomatal resistance from turgor pressure, [-]
    CanopyIsothBndlResist_pft       => plt_ew%CanopyIsothBndlResist_pft          , & !input  :canopy roughness height, [m]
    RootNonstructElmConc_rpvr => plt_biom%RootNonstructElmConc_rpvr  , & !input  :root layer nonstructural C concentration, [g g-1]
    ShootElms_pft        => plt_biom%ShootElms_pft         , & !input  :canopy shoot structural chemical element mass, [g d-2]
    SnowDepth                 => plt_ew%SnowDepth                    , & !input  :snowpack depth, [m]
    TKS_vr                    => plt_ew%TKS_vr                       , & !input  :mean annual soil temperature, [K]
    TKSnow                    => plt_ew%TKSnow                       , & !input  :snow temperature, [K]
    TairK                     => plt_ew%TairK                        , & !input  :air temperature, [K]
    ZERO                      => plt_site%ZERO                       , & !input  :threshold zero for numerical stability, [-]
    PSICanopy_pft             => plt_ew%PSICanopy_pft                , & !inoput :canopy total water potential, [Mpa]
    PSIRoot_pvr               => plt_ew%PSIRoot_pvr                  , & !inoput :root total water potential, [Mpa]
    TKC_pft                   => plt_ew%TKC_pft                      , & !inoput :canopy temperature, [K]
    RPlantRootH2OUptk_pvr   => plt_ew%RPlantRootH2OUptk_pvr      , & !output :root water uptake, [m2 d-2 h-1]
    CanPStomaResistH2O_pft    => plt_photo%CanPStomaResistH2O_pft    , & !output :canopy stomatal resistance, [h m-1]
    CanopyBndlResist_pft      => plt_photo%CanopyBndlResist_pft      , & !output :canopy boundary layer resistance, [h m-1]
    DeltaTKC_pft              => plt_ew%DeltaTKC_pft                 , & !output :change in canopy temperature, [K]
    EvapTransLHeat_pft        => plt_ew%EvapTransLHeat_pft           , & !output :canopy latent heat flux, [MJ d-2 h-1]
    HeatStorCanopy_pft        => plt_ew%HeatStorCanopy_pft           , & !output :canopy storage heat flux, [MJ d-2 h-1]
    HeatXAir2PCan_pft         => plt_ew%HeatXAir2PCan_pft            , & !output :canopy sensible heat flux, [MJ d-2 h-1]
    LWRadCanopy_pft           => plt_rad%LWRadCanopy_pft             , & !output :canopy longwave radiation, [MJ d-2 h-1]
    QdewCanopy_pft            => plt_ew%QdewCanopy_pft               , & !output :dew fall on to canopy, [m3 H2O d-2 h-1]
    RadNet2Canopy_pft         => plt_rad%RadNet2Canopy_pft           , & !output :canopy net radiation, [MJ d-2 h-1]
    TdegCCanopy_pft           => plt_ew%TdegCCanopy_pft              , & !output :canopy temperature, [oC]
    Transpiration_pft         => plt_ew%Transpiration_pft            , & !output :canopy transpiration, [m2 d-2 h-1]
    VHeatCapCanopy_pft        => plt_ew%VHeatCapCanopy_pft           , & !output :canopy heat capacity, [MJ d-2 K-1]
    VapXAir2Canopy_pft        => plt_ew%VapXAir2Canopy_pft             & !output :canopy evaporation, [m2 d-2 h-1]
  )
  RadNet2Canopy_pft(NZ)  = 0.0_r8
  EvapTransLHeat_pft(NZ)  = 0.0_r8
  HeatXAir2PCan_pft(NZ)  = 0.0_r8
  HeatStorCanopy_pft(NZ) = 0.0_r8
  VapXAir2Canopy_pft(NZ) = 0.0_r8
  Transpiration_pft(NZ)  = 0.0_r8
  QdewCanopy_pft(NZ)     = 0.0_r8
  IF(CanopyHeight_pft(NZ).GE.SnowDepth-ZERO .or. TKSnow==spval)THEN
    TKC_pft(NZ)=TairK
  ELSE
    TKC_pft(NZ)=TKSnow
  ENDIF
  TdegCCanopy_pft(NZ) = units%Kelvin2Celcius(TKC_pft(NZ))
  FTHRM                  = EMMC*stefboltz_const*FracPARads2Canopy_pft(NZ)*AREA3(NU)
  LWRadCanopy_pft(NZ)    = FTHRM*TKC_pft(NZ)**4._r8
  PSICanopy_pft(NZ)      = TotalSoilPSIMPa_vr(NGTopRootLayer_pft(NZ))
  CCPOLT                 = sum(CanopyNonstElmConc_pft(1:NumPlantChemElms,NZ))

  call update_osmo_turg_pressure(PSICanopy_pft(NZ),CCPOLT,OrganOsmoPsi0pt_pft(NZ),TKC_pft(NZ)&
    ,PSICanopyOsmo_pft(NZ),PSICanopyTurg_pft(NZ),FDMP)

  Stomata_Stress             = EXP(RCS_pft(NZ)*PSICanopyTurg_pft(NZ))
  CanPStomaResistH2O_pft(NZ) = MinCanPStomaResistH2O_pft(NZ) &
    +(H2OCuticleResist_pft(NZ)-MinCanPStomaResistH2O_pft(NZ))*Stomata_Stress
  CanopyBndlResist_pft(NZ) = CanopyIsothBndlResist_pft(NZ)
  VHeatCapCanopy_pft(NZ)     = cpw*(ShootElms_pft(ielmc,NZ)*10.0E-06_r8)
  DeltaTKC_pft(NZ)         = 0.0_r8

  DO N=1,Myco_pft(NZ)
    DO  L=NU,MaxSoiL4Root_pft(NZ)
      PSIRoot_pvr(N,L,NZ)              = TotalSoilPSIMPa_vr(L)
      CCPOLT                           = sum(RootNonstructElmConc_rpvr(1:NumPlantChemElms,N,L,NZ))
      RPlantRootH2OUptk_pvr(N,L,NZ) = 0.0_r8

      call update_osmo_turg_pressure(PSIRoot_pvr(N,L,NZ),CCPOLT,OrganOsmoPsi0pt_pft(NZ),TKS_vr(L),&
        PSIRootOSMO_vr(N,L,NZ),PSIRootTurg_vr(N,L,NZ))

    enddo
  ENDDO
  end associate
  end subroutine HandleBareSoil