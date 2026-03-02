  subroutine CalcResistance(NZ,PathLen_pvr,FineRootRadius_rvr,RootEffLen4Absorption_pvr,&
    RootResist_rvr,RootResistSoi_rvr,RootResistPrimary,RootResist2ndary,SoiH2OResist,&
    SoilRootResistance_rvr,CNDT,PSIGravCanopyHeight,SoiLayerHasRoot_rvr)

  implicit none
  integer, intent(in)   :: NZ
  real(r8), intent(in)  :: PathLen_pvr(jroots,JZ1),FineRootRadius_rvr(jroots,JZ1)
  real(r8), intent(in)  :: RootEffLen4Absorption_pvr(jroots,JZ1)
  real(r8), intent(out) :: RootResist_rvr(jroots,JZ1),RootResistSoi_rvr(jroots,JZ1)
  real(r8), intent(out) :: RootResistPrimary(jroots,JZ1),RootResist2ndary(jroots,JZ1)
  real(r8), intent(out) :: SoiH2OResist(jroots,JZ1)
  real(r8), intent(out) :: SoilRootResistance_rvr(jroots,JZ1)   !added soil and root resistance
  real(r8), intent(out) :: CNDT                   !total root conductance
  real(r8), intent(out) :: PSIGravCanopyHeight    !gravimetric water potential at CanopyHeight4WatUptake_pft, [MPa]
  logical , intent(out) :: SoiLayerHasRoot_rvr(jroots,JZ1)

  character(len=*), parameter :: subname='CalcResistance'
  real(r8) :: FRADW,FRAD1,FRAD2
  real(r8) :: RSSL,Root2ndSurfArea
  integer :: N, L
  associate(                                                                 &
    CanopyHeight_pft            => plt_morph%CanopyHeight_pft               , & !input  :canopy height, [m]
    CumSoilThickMidL_vr         => plt_site%CumSoilThickMidL_vr             , & !input  :depth to middle of soil layer from surface of grid cell, [m]
    HYCDMicP4RootUptake_vr => plt_soilchem%HYCDMicP4RootUptake_vr , & !input  :soil micropore hydraulic conductivity for root water uptake, [m MPa-1 h-1]
    MaxSoiL4Root_pft            => plt_morph%MaxSoiL4Root_pft               , & !input  :maximum soil layer number for all root axes,[-]
    Myco_pft                    => plt_morph%Myco_pft                       , & !input  :mycorrhizal type (no or yes),[-]
    NU                          => plt_site%NU                              , & !input  :current soil surface layer number, [-]
    PSICanopy_pft               => plt_ew%PSICanopy_pft                     , & !input  :canopy total water potential, [Mpa]
    PlantPopulation_pft         => plt_site%PlantPopulation_pft             , & !input  :plant population, [d-2]
    Root1stRadius_pvr           => plt_morph%Root1stRadius_pvr              , & !input  :root layer diameter primary axes, [m]
    Root1stXNumL_pvr            => plt_morph%Root1stXNumL_pvr               , & !input  :root layer number primary axes, [d-2]
    Root2ndMaxRadius_pft        => plt_morph%Root2ndMaxRadius_pft           , & !input  :maximum radius of secondary roots, [m]
    Root2ndEffLen4uptk_rpvr         => plt_morph%Root2ndEffLen4uptk_rpvr            , & !input  :root layer average length, [m]
    Root2ndRadius_rpvr           => plt_morph%Root2ndRadius_rpvr              , & !input  :root layer diameter secondary axes, [m]
    Root2ndXNumL_rpvr             => plt_morph%Root2ndXNumL_rpvr                , & !input  :root layer number axes, [d-2]
    RootAxialResist_pft         => plt_morph%RootAxialResist_pft            , & !input  :root axial resistivity, [MPa h m-4]
    RootLenDensPerPlant_pvr     => plt_morph%RootLenDensPerPlant_pvr        , & !input  :root layer length density, [m m-3]
    RootLenPerPlant_pvr         => plt_morph%RootLenPerPlant_pvr            , & !input  :root layer length per plant, [m p-1]
    RootRadialResist_pft        => plt_morph%RootRadialResist_pft           , & !input  :root radial resistivity, [MPa h m-2]
    THETW_vr                    => plt_soilchem%THETW_vr                    , & !input  :volumetric water content, [m3 m-3]
    VLMicP_vr                   => plt_soilchem%VLMicP_vr                   , & !input  :total volume in micropores, [m3 d-2]
    VLSoilPoreMicP_vr           => plt_soilchem%VLSoilPoreMicP_vr           , & !input  :volume of soil layer, [m3 d-2]
    VLWatMicPM_vr               => plt_site%VLWatMicPM_vr                   , & !input  :soil micropore water content, [m3 d-2]
    ZERO                        => plt_site%ZERO                            , & !input  :threshold zero for numerical stability, [-]
    ZERO4Groth_pft              => plt_biom%ZERO4Groth_pft                  , & !input  :threshold zero for plang growth calculation, [-]
    ZEROS2                      => plt_site%ZEROS2                          , & !input  :threshold zero for numerical stability,[-]
    CanopyHeight4WatUptake_pft  => plt_morph%CanopyHeight4WatUptake_pft       & !inoput :canopy height, [m]
  )

  !     GRAVIMETRIC WATER POTENTIAL FROM CANOPY HEIGHT
  !
  !     CanopyHeight4WatUptake_pft=canopy height for water uptake
  !     FRADW=conducting elements of stalk relative to those of primary root
  !     PSICanopy_pft=canopy total water potential
  !     EMODW=wood modulus of elasticity (MPa)
  call PrintInfo('beg '//subname)

  CNDT                           = 0.0_r8
  CanopyHeight4WatUptake_pft(NZ) = 0.80_r8*CanopyHeight_pft(NZ)
  PSIGravCanopyHeight            = mGravAccelerat*CanopyHeight4WatUptake_pft(NZ)
  FRADW                          = 1.0E+04_r8*(AMAX1(0.5_r8,1.0_r8+PSICanopy_pft(NZ)/EMODW))**4._r8
  !
  !     SOIL AND ROOT HYDRAULIC RESISTANCES TO ROOT WATER UPTAKE
  !
  !      VLSoilPoreMicP_vr,VLWatMicPM,THETW=soil,water volume,content
  !     RootLenDensPerPlant_pvr,RootLenPerPlant_pvr=root length density,root length per plant
  !     HYCDMicP4RootUptake_vr=soil hydraulic conductivity for root uptake
  !     Root1stXNumL_pvr,Root2ndXNumL_rpvr=number of root,myco primary,secondary axes
  !     SoiLayerHasRoot_rvr:1=rooted,0=not rooted
  !     N:1=root,2=mycorrhizae
!
  D3880: DO N=1,Myco_pft(NZ)
    DO  L=NU,MaxSoiL4Root_pft(NZ)

      SoiLayerHasRoot_rvr(N,L)=VLSoilPoreMicP_vr(L).GT.ZEROS2        &  
        .AND. VLWatMicPM_vr(NPH,L).GT.ZEROS2                         &
        .AND. RootLenDensPerPlant_pvr(N,L,NZ).GT.ZERO                &
        .AND. HYCDMicP4RootUptake_vr(L).GT.ZERO                 &
        .AND. Root1stXNumL_pvr(ipltroot,L,NZ).GT.ZERO4Groth_pft(NZ)  &
        .AND. Root2ndXNumL_rpvr(N,L,NZ).GT.ZERO4Groth_pft(NZ)          &
        .AND. THETW_vr(L).GT.ZERO
      if(SoiLayerHasRoot_rvr(N,L))THEN
        
        !
        !     SOIL HYDRAULIC RESISTANCE FROM RADIAL UPTAKE GEOMETRY
        !     AND SOIL HYDRAULIC CONDUCTIVITY
        !
        !     SoiH2OResist=soil hydraulic resistance
        !     PP=plant population
        !     PathLen_pvr=path length of water and nutrient uptake
        !     FineRootRadius_rvr,RootEffLen4Absorption_pvr=root radius,surface/radius area
        !
        RSSL              = (LOG(PathLen_pvr(N,L)/FineRootRadius_rvr(N,L))/RootEffLen4Absorption_pvr(N,L))/PlantPopulation_pft(NZ)
        SoiH2OResist(N,L) = RSSL/HYCDMicP4RootUptake_vr(L)
        !
        !     RADIAL ROOT RESISTANCE FROM ROOT AREA AND RADIAL RESISTIVITY
        !     ENTERED IN 'READQ'
        !
        !     Root2ndRadius_rpvr=secondary root radius
        !     RootLenPerPlant_pvr=root length per plant
        !     RootResistSoi_rvr=radial resistance
        !     RootRadialResist_pft=radial resistivity from PFT file
        !     VLMicP,VLWatMicPM=soil micropore,water volume
        !
        Root2ndSurfArea        = TwoPiCON*Root2ndRadius_rpvr(N,L,NZ)*RootLenPerPlant_pvr(N,L,NZ)*PlantPopulation_pft(NZ)
        RootResistSoi_rvr(N,L) = RootRadialResist_pft(N,NZ)/Root2ndSurfArea*VLMicP_vr(L)/VLWatMicPM_vr(NPH,L)
!
        !     ROOT AXIAL RESISTANCE FROM RADII AND LENGTHS OF PRIMARY AND
        !     SECONDARY ROOTS AND FROM AXIAL RESISTIVITY ENTERED IN 'READQ'
        !
        !     FRAD1,FRAD2=primary,secondary root radius relative to maximum
        !     secondary radius from PFT file Root2ndMaxRadius_pft at which RootAxialResist_pft is defined
        !     Root1stRadius_pvr,Root2ndRadius_rpvr=primary,secondary root radius
        !     RootAxialResist_pft=axial resistivity from PFT file
        !     DPTHZ=depth of primary root from surface
        !     RootResistPrimary,RootResist2ndary=axial resistance of primary,secondary roots
        !     Root2ndEffLen4uptk_rpvr=average secondary root length
        !     Root1stXNumL_pvr,Root2ndXNumL_rpvr=number of primary,secondary axes
        ! apply the Poiseuille relationship (Aguirrezabal et al., 1993, Grant, 1998)
        FRAD1                  = (Root1stRadius_pvr(N,L,NZ)/Root2ndMaxRadius_pft(N,NZ))**4._r8
        RootResistPrimary(N,L) = RootAxialResist_pft(N,NZ)*CumSoilThickMidL_vr(L)/(FRAD1*Root1stXNumL_pvr(ipltroot,L,NZ)) &
          +RootAxialResist_pft(ipltroot,NZ)*CanopyHeight4WatUptake_pft(NZ)/(FRADW*Root1stXNumL_pvr(ipltroot,L,NZ))

        FRAD2                = (Root2ndRadius_rpvr(N,L,NZ)/Root2ndMaxRadius_pft(N,NZ))**4._r8
        RootResist2ndary(N,L) = RootAxialResist_pft(N,NZ)*Root2ndEffLen4uptk_rpvr(N,L,NZ)/(FRAD2*Root2ndXNumL_rpvr(N,L,NZ))
        !
        !     TOTAL ROOT RESISTANCE = SOIL + RADIAL + AXIAL
        !
        !     RootResist=root radial+axial resistance
        !     SoilRootResistance_rvr=total soil+root resistance
        !     CNDT=total soil+root conductance for all layers
        ! assuming all roots work in parallel

        RootResist_rvr(N,L)         = RootResistSoi_rvr(N,L)+RootResistPrimary(N,L)+RootResist2ndary(N,L)
        SoilRootResistance_rvr(N,L) = SoiH2OResist(N,L)+RootResist_rvr(N,L)
        CNDT                        = CNDT+1.0_r8/SoilRootResistance_rvr(N,L)

      ENDIF
    enddo
  ENDDO D3880
  call PrintInfo('end '//subname)
  end associate
  end subroutine CalcResistance