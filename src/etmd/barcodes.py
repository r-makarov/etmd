from dataclasses import dataclass

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


def elder_rule(root, f, root_value=0.0):
    """Compute the barcode of the subtree rooted at a section.

    Parameters
    ----------
    root : Section
        The root of the subtree.
    f : callable
        A function that takes a section and returns a float (e.g. the path distance).
    root_value : float, optional
        The value of f at the root.

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
