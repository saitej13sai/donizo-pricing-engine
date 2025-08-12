import csv
import io
from typing import List, Dict, Iterable

def rows_to_csv(rows: Iterable[Dict], field_order: List[str]) -> str:
    """Convert list[dict] to CSV string with a fixed column order."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=field_order, extrasaction="ignore")
    writer.writeheader()
    for r in rows:
        safe = {}
        for k in field_order:
            v = r.get(k)
            if v is None:
                safe[k] = ""
            elif hasattr(v, "quantize"):  # Decimal
                safe[k] = float(v)
            else:
                safe[k] = v
        writer.writerow(safe)
    return buf.getvalue()
