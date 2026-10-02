"""ETL de validación de un Excel de postes por territorio.

Lee un .xlsx de una carpeta, valida cada registro y genera dos archivos:
  <nombre>_valid.xlsx   -> copia del original solo con los registros que pasaron todo
  <nombre>_invalid.xlsx -> registros que fallaron, con una columna PASS/FAIL por validación

Uso:
    python etl.py --input-dir sample_data --output-dir output [--file input.xlsx]
"""
import argparse
import logging
import re
import sys
from pathlib import Path

import pandas as pd

COLUMNS = ["Region", "Division", "Service Territory", "SAP_code", "abreviation", "#Poles"]
CHECKS = ["Empty_Check", "Format_Check", "SpecialChars_Check", "Duplicate_Check"]

TEXT_PATTERN = r"^[A-Za-zÀ-ÿ _-]+$"
FORMAT_PATTERNS = {
    "Region": TEXT_PATTERN,
    "Division": TEXT_PATTERN,
    "Service Territory": TEXT_PATTERN,
    "SAP_code": r"^[A-Za-z]+$",
    "abreviation": r"^[A-Z]{2}$",
    "#Poles": r"^\d+$",
}
SPECIAL_CHARS = r"[^\w\s-]"

log = logging.getLogger("etl")


def extract(path: Path) -> pd.DataFrame:
    """Lee el Excel como texto (para no perder ceros ni formatos) y valida las columnas."""
    df = pd.read_excel(path, dtype=str, keep_default_na=False)
    df.columns = [str(c).strip() for c in df.columns]
    missing = [c for c in COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas en {path.name}: {missing}")
    return df[COLUMNS]


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    return df.astype(str).apply(lambda col: col.str.strip())


def check_empty(df: pd.DataFrame) -> pd.Series:
    """True si la fila NO tiene celdas vacías."""
    return (_clean(df) != "").all(axis=1)


def check_format(df: pd.DataFrame) -> pd.Series:
    """True si todas las celdas no vacías cumplen el formato de su columna."""
    clean = _clean(df)
    ok = pd.DataFrame(index=df.index)
    for col, pattern in FORMAT_PATTERNS.items():
        ok[col] = (clean[col] == "") | clean[col].str.match(pattern)
    return ok.all(axis=1)


def check_special_chars(df: pd.DataFrame) -> pd.Series:
    """True si ninguna celda contiene caracteres especiales (fuera de letras, dígitos, espacio, _ y -)."""
    clean = _clean(df)
    has_special = clean.apply(lambda col: col.str.contains(SPECIAL_CHARS, regex=True))
    return ~has_special.any(axis=1)


def check_duplicates(df: pd.DataFrame) -> pd.Series:
    """True si la fila no es copia exacta de una anterior (la primera aparición pasa)."""
    return ~_clean(df).duplicated(keep="first")


def validate(df: pd.DataFrame) -> pd.DataFrame:
    """Devuelve el DataFrame original con una columna PASS/FAIL por validación."""
    results = {
        "Empty_Check": check_empty(df),
        "Format_Check": check_format(df),
        "SpecialChars_Check": check_special_chars(df),
        "Duplicate_Check": check_duplicates(df),
    }
    out = df.copy()
    for name in CHECKS:
        out[name] = results[name].map({True: "PASS", False: "FAIL"})
    return out


def split(validated: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    passed = (validated[CHECKS] == "PASS").all(axis=1)
    valid = validated.loc[passed, COLUMNS].reset_index(drop=True)
    invalid = validated.loc[~passed].copy()
    # Fila en el Excel original: +2 por encabezado y base 1.
    invalid.insert(0, "Excel_Row", invalid.index + 2)
    return valid, invalid.reset_index(drop=True)


def load(valid: pd.DataFrame, invalid: pd.DataFrame, stem: str, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    valid_path = output_dir / f"{stem}_valid.xlsx"
    invalid_path = output_dir / f"{stem}_invalid.xlsx"
    valid.to_excel(valid_path, index=False)
    invalid.to_excel(invalid_path, index=False)
    return valid_path, invalid_path


def find_input(input_dir: Path, filename: str | None) -> Path:
    if filename:
        path = input_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f"No existe {path}")
        return path
    files = sorted(p for p in input_dir.glob("*.xlsx") if not p.name.startswith("~$"))
    if not files:
        raise FileNotFoundError(f"No hay archivos .xlsx en {input_dir}")
    if len(files) > 1:
        log.warning("Hay %d archivos .xlsx, se usa %s (use --file para elegir)", len(files), files[0].name)
    return files[0]


def run(input_dir: Path, output_dir: Path, filename: str | None = None) -> tuple[Path, Path]:
    path = find_input(input_dir, filename)
    log.info("Leyendo %s", path)
    validated = validate(extract(path))
    valid, invalid = split(validated)
    valid_path, invalid_path = load(valid, invalid, path.stem, output_dir)

    log.info("Total: %d | válidos: %d | inválidos: %d", len(validated), len(valid), len(invalid))
    for name in CHECKS:
        log.info("%s FAIL: %d", name, (validated[name] == "FAIL").sum())
    log.info("Generados: %s, %s", valid_path, invalid_path)
    return valid_path, invalid_path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input-dir", type=Path, required=True, help="Carpeta con el Excel origen")
    parser.add_argument("--output-dir", type=Path, default=Path("output"), help="Carpeta de salida (default: output)")
    parser.add_argument("--file", help="Nombre del Excel (default: primer .xlsx de la carpeta)")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        run(args.input_dir, args.output_dir, args.file)
    except (FileNotFoundError, ValueError) as exc:
        log.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
