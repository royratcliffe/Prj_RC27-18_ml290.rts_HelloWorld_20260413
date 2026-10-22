## Excel to CSV

Requires Python 3.9 or newer. Install the converter dependency:

```powershell
python -m pip install -r .\scripts\requirements-excel.txt
```

Export the visible worksheets in `_easyConfig_import`, or specify a workbook:

```powershell
python .\scripts\excel_to_csv.py
python .\scripts\excel_to_csv.py .\_easyConfig_import\BSW-DTC-import_J1939.xlsx
python .\scripts\excel_to_csv.py .\_easyConfig_import --dry-run
```

The converter supports `.xlsx` files without Excel installed.
Use `--recurse` to include subfolders. Hidden and very-hidden sheets are skipped,
as are Excel lock files when scanning folders. Each CSV is written beside its
workbook with UTF-8 BOM encoding and comma delimiters; existing CSVs are
overwritten. A workbook with one visible sheet produces `<Workbook>.csv`;
multiple visible sheets produce `<Workbook>_<Sheet>.csv`.

Values, blank cells and column order are preserved, but Excel display formatting
(such as numeric formats) is not reproduced. Formulas export their cached results;
recalculate and save in Excel first if these are stale or missing (missing cached
results export as blank cells). Source workbooks are not modified.
