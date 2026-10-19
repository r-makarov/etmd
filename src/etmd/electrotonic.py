import numpy as np
from functools import cache


def length_constant(diam, Rm, Ra):
    """DC length constant in µm, for diam in µm, Rm in Ohm cm2 and Ra in Ohm cm."""
    diam_cm = diam * 1e-4
    lambda_cm = np.sqrt(diam_cm * Rm / (4 * Ra))
    return 1e4 * lambda_cm # cm -> um


def electrotonic_length(sec):
    """Electrotonic length of a section: sum over its segments of L_seg / lambda_seg."""
    nrn_sec = sec._ref
    L_seg = nrn_sec.L / nrn_sec.nseg # um, equal for all segments
    return sum(
        L_seg / length_constant(
            diam=seg.diam,
            Rm=1 / seg.gbar_Leak,
            Ra=nrn_sec.Ra)
        for seg in nrn_sec
    )


def electrotonic_distance(model):
    """X at the far end of each section, measured from the soma."""
    soma = model.sec_tree.soma

    @cache
    def X(sec):
        start = 0.0 if sec.parent is soma else X(sec.parent)
        return start + electrotonic_length(sec)

    return X
