"""Genera sample_data/input.xlsx con casos PASS y FAIL de cada validación del ETL."""
from pathlib import Path

import pandas as pd

from etl import COLUMNS

ROWS = [
    # --- Válidos (PASS en todo) ---
    ["Norte", "Division Alfa", "Territorio-Uno", "Alpha", "AA", "120"],
    ["Sur", "Division_Beta", "Territorio Dos", "Bravo", "BB", "0"],
    ["Este", "Division Gamma", "Territorio_Tres", "Charlie", "CC", "4500"],
    ["Oeste", "Division-Delta", "Territorio Cuatro", "Delta", "DD", "75"],
    # --- Celda vacía (Empty_Check FAIL) ---
    ["Norte", "", "Territorio-Uno", "Echo", "EE", "10"],
    ["Sur", "Division Beta", "Territorio Dos", "Foxtrot", "FF", ""],
    # --- Formato inválido (Format_Check FAIL) ---
    ["Este", "Division Gamma", "Territorio Tres", "Golf123", "GG", "30"],   # SAP_code con dígitos
    ["Oeste", "Division Delta", "Territorio Cuatro", "Hotel", "hh", "40"],  # abreviation minúscula
    ["Norte", "Division Alfa", "Territorio Uno", "India", "IND", "50"],     # abreviation 3 letras
    ["Sur", "Division Beta", "Territorio Dos", "Juliet", "JJ", "-5"],       # #Poles negativo
    ["Este", "Division Gamma", "Territorio Tres", "Kilo", "KK", "12.5"],    # #Poles decimal
    ["Oeste", "Division Delta", "Territorio Cuatro", "Lima", "LL", "abc"],  # #Poles texto
    # --- Caracteres especiales (SpecialChars_Check FAIL) ---
    ["Norte@", "Division Alfa", "Territorio Uno", "Mike", "MM", "60"],
    ["Sur", "Division Beta", "Territorio #2", "November", "NN", "70"],
    # --- Duplicado exacto de la fila 2 (Duplicate_Check FAIL en la repetición) ---
    ["Norte", "Division Alfa", "Territorio-Uno", "Alpha", "AA", "120"],
    # --- Múltiples fallas: vacío + formato + especial ---
    ["Sur$", "", "Territorio Dos", "Oscar9", "oo", "x"],
]


def main(out: Path = Path("sample_data/input.xlsx")) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(ROWS, columns=COLUMNS).to_excel(out, index=False)
    return out


if __name__ == "__main__":
    print(f"Generado {main()}")
