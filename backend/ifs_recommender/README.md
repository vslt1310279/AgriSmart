# Tamil Nadu IFS Recommender (Rule-Based)

This is a small rule-based engine that recommends **Integrated Farming System (IFS)** models for farmers in **Tamil Nadu**.

It works by:

1. Taking a user-entered **location** (village/town/city).
2. Resolving it to a **district** (via OpenStreetMap Nominatim geocoding).
3. Looking up that district in the provided CSV and returning viable **IFS models + descriptions**.

## Data source

The recommender expects the CSV with columns:

- `District`
- `Agro_Climatic_Zone`
- `IFS_Model`
- `Description`

By default it will try:

- `C:\Users\Tushaar\Downloads\ifs - TN_IFS_TNAU_Complete.csv`

You can override with `--csv`.

## Setup

```bash
cd ifs_recommender
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run (CLI)

```bash
python recommend.py --location "Chengalpattu"
```

Or provide district directly (no geocoding call):

```bash
python recommend.py --district "Chengalpattu"
```

Or specify the CSV path:

```bash
python recommend.py --csv "C:\path\to\ifs.csv" --location "Kanchipuram"
```

JSON output:

```bash
python recommend.py --location "Coimbatore" --format json
```

## Output

The CLI prints:

- detected district (if `--location` was used)
- matched CSV district name
- list of recommendations (`IFS_Model` + `Description`), grouped for that district

