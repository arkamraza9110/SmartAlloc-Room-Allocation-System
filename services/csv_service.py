"""CSV export helpers."""

import csv
import io


def csv_response(rows: list[dict], filename: str):
    output = io.StringIO()
    fieldnames = sorted({key for row in rows for key in row}) if rows else ["message"]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    if rows:
        writer.writerows(rows)
    else:
        writer.writerow({"message": "No records"})
    from flask import Response

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def parse_csv(file_storage) -> list[dict]:
    text = file_storage.read().decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))

