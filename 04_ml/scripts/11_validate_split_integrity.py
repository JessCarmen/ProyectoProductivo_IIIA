import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "04_ml/models/split_manifest.csv"


def main():
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError("No existe split_manifest.csv. Ejecuta 04_train.py primero.")

    m = pd.read_csv(MANIFEST_PATH)
    counts = m["split"].value_counts().to_dict()
    groups = {
        split: set(m.loc[m["split"] == split, "source_parent_id"].astype(str))
        for split in ["train", "validation", "test"]
    }
    overlaps = {
        "train_validation": len(groups["train"] & groups["validation"]),
        "train_test": len(groups["train"] & groups["test"]),
        "validation_test": len(groups["validation"] & groups["test"]),
    }

    print("Registros por split:", json.dumps(counts, indent=2))
    print("Grupos compartidos:", json.dumps(overlaps, indent=2))

    if any(overlaps.values()):
        raise RuntimeError("VALIDACION FALLIDA: hay source_parent_id compartidos entre particiones.")
    print("VALIDACION OK: ningun source_parent_id aparece en mas de una particion.")


if __name__ == "__main__":
    main()
