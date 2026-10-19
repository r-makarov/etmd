import json
from pathlib import Path

import dendrotweaks as dd

from etmd.barcodes import Barcode
from etmd.electrotonic import electrotonic_distance

ROOT = Path(__file__).resolve().parents[2]
PATH_TO_DATA = ROOT / 'data'
MODELS = ['Hay_2011', 'Park_2019']
DOMAIN_NAMES = {
    'Hay_2011': ['apic', 'basal'],
    'Park_2019': ['apic', 'basal'],
}


def load_model(model_name):
    path_to_model = PATH_TO_DATA / model_name
    model = dd.Model(path_to_model)
    model.load_morphology(file_name='main')
    model.load_biophys(file_name='passive')
    model.set_segmentation(d_lambda=0.1)
    return model


def path_distance(sec):
    """Return the path distance from the root of the section to the tip."""
    return sec.path_distance(relative_position=1.0)


def serialize(barcode, reference=None):
    """Serialize a barcode to a dictionary of columns, one row per bar."""
    reference_start = {bar.tip.idx: bar.start.idx for bar in (reference or barcode)}
    return {
        'birth': [bar.birth for bar in barcode],
        'death': [bar.death for bar in barcode],
        'y': list(range(len(barcode))), # row in the barcode figure
        'bar_xs': [[round(p.x, 2) for p in bar.points] for bar in barcode],
        'bar_ys': [[round(p.y, 2) for p in bar.points] for bar in barcode],
        'color': [bar.tip.domain_color for bar in barcode],
        'domain': [bar.tip.domain_name for bar in barcode],
        'tip': [int(bar.tip.idx) for bar in barcode],
        'start': [int(bar.start.idx) for bar in barcode],
        'repaired': [bar.start.idx != reference_start[bar.tip.idx] for bar in barcode],
    }


def main():
    for model_name in MODELS:
        model = load_model(model_name)
        filtrations = {'path': path_distance, 'electrotonic': electrotonic_distance(model)}

        barcodes = {}
        for name, f in filtrations.items():
            barcodes[name] = Barcode.from_model(model, f=f, domain_names=DOMAIN_NAMES[model_name])
            barcodes[name].sort()

        data = {name: serialize(barcode, reference=barcodes['path'])
                for name, barcode in barcodes.items()}
        with open(PATH_TO_DATA / model_name / 'barcodes.json', 'w') as f:
            json.dump(data, f)

        n_repaired = sum(data['electrotonic']['repaired'])
        print(f'{model_name}: {len(barcodes["path"])} bars, {n_repaired} re-paired under X')


if __name__ == '__main__':
    main()
