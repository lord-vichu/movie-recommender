import csv
import gzip
import tempfile
import time
from pathlib import Path

import requests

from django.core.management.base import BaseCommand

from movies.models import IMDbMovie


IMDB_DATASET_BASE = "https://datasets.imdbws.com"
AKAS_FILE = "title.akas.tsv.gz"
BASICS_FILE = "title.basics.tsv.gz"
RATINGS_FILE = "title.ratings.tsv.gz"


class Command(BaseCommand):
    help = "Import movie catalog from free IMDb datasets (best free non-TMDb source)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--languages",
            default="ml",
            help="Comma-separated language codes from IMDb akas (default: ml)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Optional max number of movies to import (0 = no limit)",
        )
        parser.add_argument(
            "--refresh",
            action="store_true",
            help="Delete existing IMDbMovie rows before import",
        )

    def handle(self, *args, **options):
        languages = {lang.strip().lower() for lang in options["languages"].split(",") if lang.strip()}
        limit = options["limit"]
        refresh = options["refresh"]

        if refresh:
            deleted, _ = IMDbMovie.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted} existing IMDbMovie rows"))

        with tempfile.TemporaryDirectory(prefix="imdb_import_") as tmp_dir:
            tmp_path = Path(tmp_dir)

            akas_path = self._download(tmp_path, AKAS_FILE)
            selected_ids, countries_by_id = self._collect_ids_from_akas(akas_path, languages)
            self.stdout.write(f"Selected IDs from akas: {len(selected_ids)}")

            if not selected_ids:
                self.stdout.write(self.style.WARNING("No IMDb IDs found for selected languages"))
                return

            basics_path = self._download(tmp_path, BASICS_FILE)
            movies_by_id = self._collect_movies_from_basics(basics_path, selected_ids)
            self.stdout.write(f"Movie rows from basics: {len(movies_by_id)}")

            if not movies_by_id:
                self.stdout.write(self.style.WARNING("No movie rows matched selected IDs"))
                return

            ratings_path = self._download(tmp_path, RATINGS_FILE)
            ratings_by_id = self._collect_ratings(ratings_path, set(movies_by_id.keys()))

            imported = self._upsert_movies(
                movies_by_id=movies_by_id,
                ratings_by_id=ratings_by_id,
                countries_by_id=countries_by_id,
                languages=languages,
                limit=limit,
            )

            self.stdout.write(self.style.SUCCESS(f"IMDb import complete: {imported} movies upserted"))

    def _download(self, tmp_path: Path, filename: str) -> Path:
        url = f"{IMDB_DATASET_BASE}/{filename}"
        destination = tmp_path / filename
        self.stdout.write(f"Downloading {filename} ...")

        retries = 3
        for attempt in range(1, retries + 1):
            try:
                with requests.get(url, stream=True, timeout=60) as response:
                    response.raise_for_status()
                    expected_size = int(response.headers.get("Content-Length", "0") or 0)

                    with open(destination, "wb") as file_handle:
                        for chunk in response.iter_content(chunk_size=1024 * 1024):
                            if chunk:
                                file_handle.write(chunk)

                downloaded_size = destination.stat().st_size if destination.exists() else 0
                if expected_size and downloaded_size < expected_size:
                    raise IOError(
                        f"Incomplete download: expected {expected_size} bytes, got {downloaded_size} bytes"
                    )

                return destination
            except Exception as error:
                if destination.exists():
                    destination.unlink(missing_ok=True)

                if attempt == retries:
                    raise RuntimeError(f"Failed downloading {filename} after {retries} attempts") from error

                wait_seconds = attempt * 2
                self.stdout.write(
                    self.style.WARNING(
                        f"Download failed for {filename} (attempt {attempt}/{retries}): {error}. Retrying in {wait_seconds}s..."
                    )
                )
                time.sleep(wait_seconds)

        return destination

    def _collect_ids_from_akas(self, akas_path: Path, languages):
        selected_ids = set()
        countries_by_id = {}

        with gzip.open(akas_path, mode="rt", encoding="utf-8", newline="") as gz_file:
            reader = csv.DictReader(gz_file, delimiter="\t")
            for row in reader:
                language = (row.get("language") or "").strip().lower()
                if language not in languages:
                    continue

                tconst = (row.get("titleId") or "").strip()
                if not tconst:
                    continue

                selected_ids.add(tconst)
                region = (row.get("region") or "").strip()
                if region and region != "\\N":
                    countries_by_id.setdefault(tconst, set()).add(region)

        return selected_ids, countries_by_id

    def _collect_movies_from_basics(self, basics_path: Path, selected_ids):
        movies_by_id = {}

        with gzip.open(basics_path, mode="rt", encoding="utf-8", newline="") as gz_file:
            reader = csv.DictReader(gz_file, delimiter="\t")
            for row in reader:
                tconst = (row.get("tconst") or "").strip()
                if tconst not in selected_ids:
                    continue

                title_type = (row.get("titleType") or "").strip()
                is_adult = (row.get("isAdult") or "").strip()
                if title_type not in {"movie", "tvMovie"} or is_adult != "0":
                    continue

                year_raw = (row.get("startYear") or "").strip()
                year = int(year_raw) if year_raw.isdigit() else None

                genres_raw = (row.get("genres") or "").strip()
                genres = []
                if genres_raw and genres_raw != "\\N":
                    genres = [genre.strip() for genre in genres_raw.split(",") if genre.strip()]

                movies_by_id[tconst] = {
                    "tconst": tconst,
                    "title": (row.get("primaryTitle") or "").strip(),
                    "original_title": (row.get("originalTitle") or "").strip(),
                    "year": year,
                    "genres": genres,
                }

        return movies_by_id

    def _collect_ratings(self, ratings_path: Path, target_ids):
        ratings_by_id = {}

        with gzip.open(ratings_path, mode="rt", encoding="utf-8", newline="") as gz_file:
            reader = csv.DictReader(gz_file, delimiter="\t")
            for row in reader:
                tconst = (row.get("tconst") or "").strip()
                if tconst not in target_ids:
                    continue

                rating_raw = (row.get("averageRating") or "").strip()
                votes_raw = (row.get("numVotes") or "").strip()

                rating = float(rating_raw) if rating_raw not in {"", "\\N"} else None
                votes = int(votes_raw) if votes_raw.isdigit() else 0

                ratings_by_id[tconst] = {
                    "rating": rating,
                    "votes": votes,
                }

        return ratings_by_id

    def _upsert_movies(self, movies_by_id, ratings_by_id, countries_by_id, languages, limit=0):
        imported = 0

        for tconst, movie in movies_by_id.items():
            rating_data = ratings_by_id.get(tconst, {})
            countries = sorted(countries_by_id.get(tconst, set()))

            IMDbMovie.objects.update_or_create(
                tconst=tconst,
                defaults={
                    "title": movie["title"],
                    "original_title": movie["original_title"],
                    "year": movie["year"],
                    "language": next(iter(languages)) if len(languages) == 1 else "multi",
                    "countries": ",".join(countries),
                    "genres": movie["genres"],
                    "rating": rating_data.get("rating"),
                    "votes": rating_data.get("votes", 0),
                    "plot": "",
                },
            )

            imported += 1
            if limit and imported >= limit:
                break

        return imported
