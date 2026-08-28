# Data

The project does not commit raw CelesTrak CSV files by default.

The notebook downloads current GP data directly from CelesTrak each time it is re-run. Because the catalog changes over time, the numerical results may differ from the cached notebook outputs.

If you choose to save local CSV snapshots, place them in this folder. They are ignored by `.gitignore` by default.
