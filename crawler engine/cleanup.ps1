Get-ChildItem -Recurse -Force -Directory -Filter __pycache__ |
    Where-Object { $_.FullName -notmatch '\\.venv\\' } |
    Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Force -File -Include *.pyc,*.pyo |
    Where-Object { $_.FullName -notmatch '\\.venv\\' } |
    Remove-Item -Force
