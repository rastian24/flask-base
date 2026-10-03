"""Versión simplificada de etl.py: valida sample_data/input.xlsx y genera
output/input_valid.xlsx y output/input_invalid.xlsx.

Uso:
    python etl_simple.py
"""
from pathlib import Path

import pandas as pd


def main():
    input_path = Path("sample_data/input.xlsx")
    output_dir = Path("output")

    columns = ["Region", "Division", "Service Territory", "SAP_code", "abreviation", "#Poles"]
    checks = ["Empty_Check", "Format_Check", "SpecialChars_Check", "Duplicate_Check"]
    text_pattern = r"^[A-Za-z _-]+$"
    format_patterns = {
        "Region": text_pattern,
        "Division": text_pattern,
        "Service Territory": text_pattern,
        "SAP_code": r"^[A-Za-z]+$",
        "abreviation": r"^[A-Z]{2}$",
        "#Poles": r"^\d+$",
    }

    # Extract: se lee todo como texto para no perder ceros ni formatos
    print(f"Leyendo {input_path}")
    df = pd.read_excel(input_path, dtype=str, keep_default_na=False)
    clean_columns = []
    for c in df.columns:
        clean_columns.append(str(c).strip())
    df.columns = clean_columns
    df = df[columns]
    clean = df.apply(lambda col: col.str.strip())

    # Validaciones
    empty_ok = (clean != "").all(axis=1)

    format_ok = pd.Series(True, index=df.index)
    for col, pattern in format_patterns.items():
        format_ok &= (clean[col] == "") | clean[col].str.match(pattern)

    special_ok = ~clean.apply(lambda col: col.str.contains(r"[^\w\s-]", regex=True)).any(axis=1)

    duplicate_ok = ~clean.duplicated(keep="first")

    validated = df.copy()
    for name, result in zip(checks, [empty_ok, format_ok, special_ok, duplicate_ok]):
        validated[name] = result.map({True: "PASS", False: "FAIL"})

    # Separar válidos e inválidos
    passed = (validated[checks] == "PASS").all(axis=1)
    valid = validated.loc[passed, columns].reset_index(drop=True)
    invalid = validated.loc[~passed].copy()
    # Fila en el Excel original: +2 por encabezado y base 1.
    invalid.insert(0, "Excel_Row", invalid.index + 2)
    invalid = invalid.reset_index(drop=True)

    # Load
    output_dir.mkdir(parents=True, exist_ok=True)
    valid_path = output_dir / f"{input_path.stem}_valid.xlsx"
    invalid_path = output_dir / f"{input_path.stem}_invalid.xlsx"
    valid.to_excel(valid_path, index=False)
    invalid.to_excel(invalid_path, index=False)

    print(f"Total: {len(validated)} | válidos: {len(valid)} | inválidos: {len(invalid)}")
    for name in checks:
        print(f"{name} FAIL: {(validated[name] == 'FAIL').sum()}")
    print(f"Generados: {valid_path}, {invalid_path}")


if __name__ == "__main__":
    main()
