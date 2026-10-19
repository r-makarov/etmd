# etmd: electrotonic barcodes of dendritic trees

Topological morphology descriptor (TMD) barcodes of dendritic trees ([Kanari et al., 2018](https://doi.org/10.1007/s12021-017-9341-1)), computed on [DendroTweaks](https://doi.org/10.7554/eLife.103324) section trees under two filtrations: 
- path distance from the soma, as in the [TMD package](https://tmd.readthedocs.io/en/latest/index.html)
- electrotonic distance, which measures length in units of the local length constant of the passive cable

## Interactive page

👉 [Barcode explorer](https://r-makarov.github.io/etmd/), built with Bokeh.

## Method

For a tree rooted at the soma and a function $f$ that increases away from the root, each tip starts a bar with birth $f(\text{tip})$.
At each branch point, the bar from the child with the largest value of $f$ continues (the elder rule). The other ends at this point, with death $f(\text{branch point})$.

- **Path distance:** path distance along the dendrite. The barcodes match those of the `tmd` package.
- **Electrotonic distance:** $X = \sum \dfrac{\Delta x}{\lambda}$ along the path from the soma, summed over the segments of the NEURON model, with the DC length constant $\lambda = \sqrt{\dfrac{d R_m}{4 R_a}}$ and $R_m = \dfrac{1}{g_{l}}$ of each segment.

A bar is *re-paired* when, under a different filtration, its tip's bar starts at a different section than under path distance i.e. the filtration changes which branch survives at a branch point.

## Repository structure

```
data/
├── Hay_2011/
│   ├── morphology/
│   │   └── main.swc              # morphology reconstruction
│   ├── biophys/passive.json      # passive properties of the published model
│   └── barcodes.json             # barcodes, written by prepare_data.py
└── Park_2019/                    # same layout
docs/
└── index.html                    # interactive page, written by page.py
notebooks/
├── tmd_baseline.ipynb            # reference barcodes of one cell with tmd
├── elder_rule.ipynb              # the elder rule step by step, compared with tmd
└── electrotonic_barcodes.ipynb   # path-distance and electrotonic barcodes of one cell
src/etmd/
├── barcodes.py                   # elder rule, Bar and Barcode
├── electrotonic.py               # electrotonic distance X
├── prepare_data.py               # writes data/<cell>/barcodes.json
└── page.py                       # builds docs/index.html
environment.yml
```

Cells from the DendroTweaks examples, with the passive properties of the published models:
- L5 pyramidal neuron ([Hay et al., 2011](https://doi.org/10.1371/journal.pcbi.1002107)) and - L2/3 pyramidal neuron ([Park et al., 2019](https://doi.org/10.1038/s41467-019-13029-0)), 

## Usage

```bash
conda env create -f environment.yml
conda activate etmd
cd src
python -m etmd.prepare_data # creates data/<cell>/barcodes.json
python -m etmd.page # cretes docs/index.html
```

## References

1. Kanari L., Dłotko P., Scolamiero M., Levi R., Shillcock J., Hess K., Markram H. (2018). A topological representation of branching neuronal morphologies. *Neuroinformatics* 16:3–13. [doi:10.1007/s12021-017-9341-1](https://doi.org/10.1007/s12021-017-9341-1)
2. Kanari L., Garin A., Hess K. (2020). From trees to barcodes and back again: theoretical and statistical perspectives. *Algorithms* 13:335. [doi:10.3390/a13120335](https://doi.org/10.3390/a13120335)
3. TMD: the topological morphology descriptor, Python package. [tmd.readthedocs.io](https://tmd.readthedocs.io/en/latest/index.html)
4. Makarov R., Chavlis S., Poirazi P. (2024). DendroTweaks, an interactive approach for unraveling dendritic dynamics. *eLife* 13:RP103324. [doi:10.7554/eLife.103324](https://doi.org/10.7554/eLife.103324)
5. Hay E., Hill S., Schürmann F., Markram H., Segev I. (2011). Models of neocortical layer 5b pyramidal cells capturing a wide range of dendritic and perisomatic active properties. *PLoS Computational Biology* 7:e1002107. [doi:10.1371/journal.pcbi.1002107](https://doi.org/10.1371/journal.pcbi.1002107)
6. Park J., Papoutsi A., Ash R. T., Marin M. A., Poirazi P., Smirnakis S. M. (2019). Contribution of apical and basal dendrites to orientation encoding in mouse V1 L2/3 pyramidal neurons. *Nature Communications* 10:5372. [doi:10.1038/s41467-019-13029-0](https://doi.org/10.1038/s41467-019-13029-0)

## Licence

MIT
