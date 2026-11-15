"""Colours and plot style shared by the figures of notebooks 03-05."""

import matplotlib as mpl
from cycler import cycler

# Series colours, always in this order. The first three stay distinguishable for colour-blind readers.
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
INK = "#0b0b0b"        # titles, reference lines
MUTED = "#898781"      # context
SURFACE = "#fcfcfb"    # figure background


def apply():
    """Quiet axes and grid, so that the data stand out."""
    mpl.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.prop_cycle": cycler(color=COLORS),
        "axes.edgecolor": "#c3c2b7", "axes.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "axes.axisbelow": True, "grid.color": "#e1e0d9", "grid.linewidth": 0.8,
        "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlelocation": "left", "axes.titlecolor": INK,
        "axes.labelcolor": "#52514e", "xtick.color": "#52514e", "ytick.color": "#52514e",
        "xtick.labelsize": 9, "ytick.labelsize": 9, "font.size": 10, "lines.linewidth": 2,
        "legend.frameon": False, "legend.fontsize": 9, "figure.dpi": 110, "savefig.dpi": 200, "savefig.bbox": "tight",
    })
