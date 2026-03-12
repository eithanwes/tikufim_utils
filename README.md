# tikufim_utils

Python utilities for passenger-count processing.

Installation (editable, per-venv):

1. create and activate your venv

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. install editable copy

```powershell
pip install -e path\to\tikufim_utils
```

Usage:

```python
from tikufim_utils import get_daily_counts

# call functions as needed
```

Notes:
- Install once per venv (editable install links to source folder).
- Keep data files (e.g., station lists) alongside the package or provide paths in your code.
