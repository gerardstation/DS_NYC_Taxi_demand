from pathlib import Path
import urllib.request

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

MONTH = "2024-01"  

YELLOW_URL = f"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{MONTH}.parquet"
ZONE_LOOKUP_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"

def download(url: str, out_path: Path) -> None:
    if out_path.exists():
        print(f"[skip] {out_path} ya existe")
        return
    print(f"[download] {url}")
    urllib.request.urlretrieve(url, out_path)
    print(f"[ok] {out_path}")

def main():
    download(YELLOW_URL, RAW_DIR / f"yellow_tripdata_{MONTH}.parquet")
    download(ZONE_LOOKUP_URL, RAW_DIR / "taxi_zone_lookup.csv")

if __name__ == "__main__":
    main()
