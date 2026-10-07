import requests
import json

# 1. List notebooks
r = requests.get('http://127.0.0.1:8000/notebooks')
notebooks = r.json()
print(f'Found {len(notebooks)} notebooks:')
for nb in notebooks:
    print(f'  ID={nb["id"]} name="{nb["name"]}"')

# 2. For each notebook, list sources
for nb in notebooks:
    nb_id = nb['id']
    r2 = requests.get(f'http://127.0.0.1:8000/notebooks/{nb_id}/sources')
    sources = r2.json()
    print(f'\n  Notebook {nb_id} sources ({len(sources)}):')
    for src in sources:
        print(f'    ID={src["id"]} type={src.get("source_type","?")} title="{src.get("title","?")}" chunks={src.get("chunk_count","?")}')
