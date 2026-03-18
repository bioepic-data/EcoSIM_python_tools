def koppen_beck(climate):
    """
    climate is a struct containing climatology data at the site.
    """
    # pre-calculations
    #mean annual air temperature [Celcius]
    MAT = climate.ts.sum() / 12
    #annual precipitation
    MAP = climate.pr.sum()
    #dryness index
    Pdry = climate.pr.min()
    #cold index
    Tcold = climate.ts.min()
    #hot index
    Thot = climate.ts.max()
    Tmon10 = 0

    for temp in climate.ts:
        if temp > 10:
            Tmon10 += 1

    if climate.lat < 0.:  # southern hemisphere, winter from the 3rd to 9th month
        he = "S"
        if climate.pr[3:9].sum() > 0.7 * MAP:
            Pth = 2 * MAT
        elif numpy.concatenate((climate.pr[0:3], climate.pr[9:12])).sum() > 0.7 * MAP:  # summer
            Pth = 2 * MAT + 28
        else:
            Pth = 2 * MAT + 14
        Pwdry = climate.pr[3:9].min()
        Pwwet = climate.pr[3:9].max()
        Psdry = numpy.concatenate((climate.pr[0:3], climate.pr[9:12])).min()
        Pswet = numpy.concatenate((climate.pr[0:3], climate.pr[9:12])).max()
    else:  # northern hemisphere, summer from the 3rd to 9th month
        he = "N"
        if numpy.concatenate((climate.pr[0:3], climate.pr[9:12])).sum() > 0.7 * MAP:
            Pth = 2 * MAT
        elif climate.pr[3:9].sum() > 0.7 * MAP:  # summer
            Pth = 2 * MAT + 28
        else:
            Pth = 2 * MAT + 14
        Psdry = climate.pr[3:9].min()
        Pswet = climate.pr[3:9].max()
        Pwdry = numpy.concatenate((climate.pr[0:3], climate.pr[9:12])).min()
        Pwwet = numpy.concatenate((climate.pr[0:3], climate.pr[9:12])).max()


    # classification conditionals
    if MAP < 10 * Pth:
        koppenClass = "B"
        if MAP < 5 * Pth:
            koppenClass = koppenClass + "W"
        else:
            koppenClass = koppenClass + "S"
        if MAT >= 18:
            koppenClass = koppenClass + "h"
        else:
            koppenClass = koppenClass + "k"
    elif Tcold >= 18:
        koppenClass = "A"
        if Pdry >= 60:
            koppenClass = koppenClass + "f"
        else:
            if Pdry >= 100 - MAP / 25:
                koppenClass = koppenClass + "m"
            else:
                koppenClass = koppenClass + "w"
# there is litter difference in Aw and As, so As is not defined
    elif Thot > 10. and 0. < Tcold < 18.:
        koppenClass = "C"
        if Psdry < 40. and Psdry < Pwwet / 3:
            koppenClass = koppenClass + "s"
        elif Pwdry < Pswet / 10.:
            koppenClass = koppenClass + "w"
        else:
            koppenClass = koppenClass + "f"
        if Thot >= 22.:
            koppenClass = koppenClass + "a"
        else:
            if Tmon10 >= 4.:
                koppenClass = koppenClass + "b"
            elif 1. <= Tmon10 < 4.:
                koppenClass = koppenClass + "c"
    elif Thot > 10. and Tcold <= 0.:
        koppenClass = "D"
        if Psdry < 40. and Psdry < Pwwet / 3.:
            koppenClass = koppenClass + "s"
        elif Pwdry < Pswet / 10.:
            koppenClass = koppenClass + "w"
        else:
            koppenClass = koppenClass + "f"
        if Thot >= 22.:
            koppenClass = koppenClass + "a"
        else:
            if Tmon10 >= 4.:
                koppenClass = koppenClass + "b"
            elif Tcold < -38.:
                koppenClass = koppenClass + "d"
            else:
                koppenClass = koppenClass + "c"
    elif Thot <= 10.:
        koppenClass = "E"
        if Thot > 0.:
            koppenClass = koppenClass + "T"
        else:
            koppenClass = koppenClass + "F"

    koppenDict = {
        "Af":  11,
        "Am":  12,
        "As":  13,
        "Aw":  14,
        "BWk": 21,
        "BWh": 22,
        "BSk": 26,
        "BSh": 27,
        "Cfa": 31,
        "Cfb": 32,
        "Cfc": 33,
        "Csa": 34,
        "Csb": 35,
        "Csc": 36,
        "Cwa": 37,
        "Cwb": 38,
        "Cwc": 39,
        "Dfa": 41,
        "Dfb": 42,
        "Dfc": 43,
        "Dfd": 44,
        "Dsa": 45,
        "Dsb": 46,
        "Dsc": 47,
        "Dsd": 48,
        "Dwa": 49,
        "Dwb": 50,
        "Dwc": 51,
        "Dwd": 52,
        "ET": 61,
        "EF": 62
    }
    return koppenDict[koppenClass]
