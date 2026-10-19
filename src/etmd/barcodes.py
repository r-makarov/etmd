from dataclasses import dataclass, replace
from functools import cached_property
import numpy as np

# ======================================================================
# BARS
# ======================================================================

@dataclass(frozen=True)
class Bar:
    """One bar of a barcode.

    Attributes
    ----------
    birth : float
        f at the tip that started the component.
    death : float
        f at the branch point where the component merged into an older one,
        or at the root for the component that survives.
    tip : Section
        The terminal section whose distal end gives the birth value.
    start : Section
        The section whose proximal end is the branch point where the bar ends.
    """
    birth: float
    death: float
    tip: object
    start: object

    @property
    def persistence(self):
        return abs(self.birth - self.death)

    @property
    def path(self):
        """Return the path of sections from the tip to the start."""
        return self.tip.path_to_ancestor(self.start)

    @cached_property
    def points(self):
        """Return the 3D points of the path that the bar represents."""
        return [p for sec in self.path for p in reversed(sec.points)]


def elder_rule(root, f):
    """Compute the barcode of the subtree rooted at a section.

    Parameters
    ----------
    root : Section
        The root of the subtree.
    f : callable
        A function that takes a section and returns a float (e.g. the path distance).

    Returns
    -------
    bars : list of Bar
        The bars of the barcode.
    survivors : dict
        A dictionary mapping each section to its oldest surviving child.
    """

    alive = {}
    bars = []
    survivors = {}

    for sec in reversed(root.subtree):

        # 1. Collect the terminations
        if not sec.children:
            alive[sec] = (sec, f(sec))
            continue
        # Otherwise, it is a branch point.
        # Find the oldest child and convert the younger siblings into bars.

        # 2. Find the oldest child
        incoming = [(child, alive.pop(child)) for child in sec.children]
        oldest_child, oldest_path = max(incoming, key=lambda x: x[1][1])
        
        # 3. Convert the younger siblings into bars
        for child, (tip, value) in incoming:
            if child is not oldest_child:
                bars.append(Bar(
                    birth=value,
                    death=f(sec),
                    tip=tip,
                    start=child
                ))
        # 4. Move the pointer of the surviving path: oldest_child -> sec
        alive[sec] = oldest_path
        # 5. Track the survivors
        if len(incoming) > 1:
            survivors[sec] = oldest_child

    tip, value = alive.pop(root)
    parent = root.parent
    root_value = 0.0 if parent.parent is None else f(parent)
    bars.append(Bar(
        birth=value,
        death=root_value,
        tip=tip,
        start=root
    ))

    return bars, survivors


def sort_bars(bars):
    """Sort bars by birth - death in ascending order."""
    return sorted(bars, key=lambda bar: bar.birth - bar.death)



# ======================================================================
# BARCODE
# ======================================================================

@dataclass(frozen=True)
class Barcode:
    """A collection of bars, representing the barcode of a tree."""
    bars: list[Bar]

    @classmethod
    def from_model(cls, model, f, domain_names):
        """Barcode of all neurites of the given domains attached to the soma."""
        roots = [sec for sec in model.sec_tree.soma.children
                 if sec.domain_name in domain_names]
        return cls.from_roots(roots, f)

    @classmethod
    def from_roots(cls, roots, f):
        """Create a barcode from a list of roots."""
        all_bars = []
        for root in roots:
            bars, _ = elder_rule(root, f)
            all_bars.extend(bars)
        return cls(all_bars)

    def __iter__(self):
        return iter(self.bars)

    def __len__(self):
        return len(self.bars)

    def __add__(self, other):
        return Barcode(self.bars + other.bars)

    def __getitem__(self, index):
        return self.bars[index]

    def sort(self):
        """Sort the bars in place by birth - death, ascending, as tmd.analysis.sort_ph does."""
        self.bars.sort(key=lambda bar: bar.birth - bar.death)

    def select(self, domain_name):
        return Barcode([bar for bar in self.bars if bar.tip.domain_name == domain_name])

    def normalized(self):
        scale = max(bar.birth for bar in self.bars)
        return Barcode([replace(bar, birth=bar.birth / scale, death=bar.death / scale)
                             for bar in self.bars])

    def by_tip(self):
        return {bar.tip: bar for bar in self.bars}

    def to_numpy(self):
        """(n, 2) array of [birth, death], as tmd returns."""
        return np.array([[bar.birth, bar.death] for bar in self.bars])
