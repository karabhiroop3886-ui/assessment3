import csv
import os
import re
from collections import defaultdict

# Custom Exceptions


class InvalidHeaderException(Exception):
    pass


class InvalidAssetCodeException(Exception):
    pass



# Constants


EXPECTED_HEADERS = [
    "asset_code",
    "day_no",
    "asset_type",
    "filename",
    "owner_email",
    "tags"
]

VALID_TYPES = {"image", "video", "css", "js", "csv"}

MANIFEST_FILE = "assets_manifest.csv"
ASSET_FOLDER = "assets"

EMAIL_REGEX = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
ASSET_REGEX = r'^A-\d{3}$'



# Recursive Function


def flatten_tags(tag_list):

    if not tag_list:
        return []

    return [tag_list[0]] + flatten_tags(tag_list[1:])



# Read Manifest


valid_assets = []

warnings = []
duplicates = []
missing_files = []
orphan_files = []
invalid_rows = []

asset_codes = {}
filename_map = {}

grouped_assets = defaultdict(lambda: defaultdict(list))


with open(MANIFEST_FILE, newline="") as file:

    reader = csv.DictReader(file)

    if reader.fieldnames != EXPECTED_HEADERS:
        raise InvalidHeaderException("Invalid CSV Headers")

    rows = list(reader)



# Process Rows


for row in rows:

    try:

        code = row["asset_code"]

        if not re.match(ASSET_REGEX, code):
            raise InvalidAssetCodeException(code)

        day = int(row["day_no"])

        asset_type = row["asset_type"]

        filename = row["filename"]

        email = row["owner_email"]

        tags = flatten_tags(row["tags"].split("|"))

        # Email Validation
        if not re.match(EMAIL_REGEX, email):
            invalid_rows.append(f"Invalid Email -> {code}")
            continue

        # Asset Type
        if asset_type not in VALID_TYPES:
            invalid_rows.append(f"Invalid Type -> {code}")
            continue

        # Day Validation
        if not (1 <= day <= 40):
            invalid_rows.append(f"Invalid Day -> {code}")
            continue

        # Warning
        if day > 30:
            warnings.append(f"{code} assigned to Day {day}")

        # Duplicate Asset Code
        if code in asset_codes:
            duplicates.append(f"Duplicate Asset Code : {code}")
            continue
        else:
            asset_codes[code] = filename

        # Conflicting Filename
        if filename in filename_map:
            duplicates.append(f"Conflicting Filename : {filename}")
            continue
        else:
            filename_map[filename] = code

        grouped_assets[day][asset_type].append(row)

        valid_assets.append(row)

    except InvalidAssetCodeException:
        invalid_rows.append(f"Invalid Asset Code -> {row['asset_code']}")




# Compare Files


manifest_files = {row["filename"] for row in valid_assets}

folder_files = set(os.listdir(ASSET_FOLDER))

missing_files = manifest_files - folder_files

orphan_files = folder_files - manifest_files



# Deployment Ready Manifest


deployment_assets = [
    row for row in valid_assets
    if row["filename"] not in missing_files
]

# Lambda Sorting
deployment_assets = sorted(
    deployment_assets,
    key=lambda x: (int(x["day_no"]), x["asset_code"])
)


with open("deployment_ready_manifest.csv", "w", newline="") as file:

    writer = csv.DictWriter(file, fieldnames=EXPECTED_HEADERS)

    writer.writeheader()

    writer.writerows(deployment_assets)



# Report


with open("reconciliation_report.txt", "w") as report:

    report.write("TRAINING ASSET RECONCILIATION REPORT\n")
    report.write("=" * 40 + "\n\n")

    report.write(f"Valid Assets : {len(deployment_assets)}\n")
    report.write(f"Invalid Rows : {len(invalid_rows)}\n")
    report.write(f"Warnings : {len(warnings)}\n")
    report.write(f"Duplicate Issues : {len(duplicates)}\n")
    report.write(f"Missing Files : {len(missing_files)}\n")
    report.write(f"Orphan Files : {len(orphan_files)}\n\n")

    report.write("Warnings\n")
    report.write("-" * 20 + "\n")
    for item in warnings:
        report.write(item + "\n")

    report.write("\nDuplicate Issues\n")
    report.write("-" * 20 + "\n")
    for item in duplicates:
        report.write(item + "\n")

    report.write("\nInvalid Rows\n")
    report.write("-" * 20 + "\n")
    for item in invalid_rows:
        report.write(item + "\n")

    report.write("\nMissing Files\n")
    report.write("-" * 20 + "\n")
    for item in missing_files:
        report.write(item + "\n")

    report.write("\nOrphan Files\n")
    report.write("-" * 20 + "\n")
    for item in orphan_files:
        report.write(item + "\n")

print("Reconciliation Complete!")
print("Generated deployment_ready_manifest.csv")
print("Generated reconciliation_report.txt")