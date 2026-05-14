"""
Seed verification test suite.
Validates that the database is properly seeded with reference images and metadata.
Runs assertions and prints a formatted report.

Usage:
    python database/tests/verify_seed.py

Exits 0 on all tests pass, 1 on any failure.
"""

import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from database.db import get_connection


class TestResult:
    def __init__(self, name, passed, details="", expected="", actual=""):
        self.name = name
        self.passed = passed
        self.details = details
        self.expected = expected
        self.actual = actual


def run_tests():
    """Run all verification tests."""
    conn = get_connection(autocommit=True)
    cur = conn.cursor()
    results = []
    
    # ──────────────────────────────────────────────
    # Test 1: Total image count
    # ──────────────────────────────────────────────
    cur.execute("SELECT COUNT(*) FROM reference_images;")
    total_images = cur.fetchone()[0]
    results.append(TestResult(
        "Total image count",
        total_images >= 100,
        f"Found {total_images} images in reference_images",
        ">= 100",
        str(total_images),
    ))
    
    # ──────────────────────────────────────────────
    # Test 2: Image count per room type
    # ──────────────────────────────────────────────
    cur.execute("""
        SELECT room_type, COUNT(*) as cnt 
        FROM reference_images 
        GROUP BY room_type 
        ORDER BY cnt DESC;
    """)
    room_counts = dict(cur.fetchall())
    min_room_count = min(room_counts.values()) if room_counts else 0
    results.append(TestResult(
        "Room type coverage",
        len(room_counts) >= 6,
        f"Room types: {dict(room_counts)}",
        ">= 6 distinct room types",
        str(len(room_counts)),
    ))
    
    # ──────────────────────────────────────────────
    # Test 3: Style coverage
    # ──────────────────────────────────────────────
    cur.execute("""
        SELECT DISTINCT unnest(style_tags) as style 
        FROM reference_images 
        ORDER BY style;
    """)
    styles = [row[0] for row in cur.fetchall()]
    results.append(TestResult(
        "Style tag coverage",
        len(styles) >= 6,
        f"Styles: {styles}",
        ">= 6 distinct styles",
        str(len(styles)),
    ))
    
    # ──────────────────────────────────────────────
    # Test 4: Text retrieval RPC present (FTS candidate pool)
    # ──────────────────────────────────────────────
    cur.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.routines
            WHERE routine_schema = 'public'
              AND routine_name = 'retrieve_candidates_text'
        );
    """)
    has_fts_rpc = cur.fetchone()[0]
    results.append(TestResult(
        "retrieve_candidates_text RPC",
        bool(has_fts_rpc),
        "Full-text candidate pool RPC (see n8n migration 012 / supabase 010)",
        "true",
        str(has_fts_rpc),
    ))
    
    # ──────────────────────────────────────────────
    # Test 5: Quality score distribution
    # ──────────────────────────────────────────────
    cur.execute("""
        SELECT 
            AVG(quality_score) as mean,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY quality_score) as median,
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY quality_score) as p25,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY quality_score) as p75,
            MIN(quality_score) as min_q,
            MAX(quality_score) as max_q
        FROM reference_images;
    """)
    stats = cur.fetchone()
    median_quality = float(stats[1]) if stats[1] else 0
    results.append(TestResult(
        "Quality score (median >= 0.8)",
        median_quality >= 0.8,
        f"Mean={stats[0]:.3f}, Median={median_quality:.3f}, P25={float(stats[2]):.3f}, P75={float(stats[3]):.3f}",
        ">= 0.8 median",
        f"{median_quality:.3f}",
    ))
    
    # ──────────────────────────────────────────────
    # Test 6: Caption metadata (non-null)
    # ──────────────────────────────────────────────
    cur.execute("SELECT COUNT(*) FROM reference_images WHERE caption IS NOT NULL AND caption != '';")
    caption_count = cur.fetchone()[0]
    results.append(TestResult(
        "Caption metadata",
        caption_count == total_images,
        f"{caption_count}/{total_images} images have captions",
        f"= {total_images} (100%)",
        str(caption_count),
    ))
    
    # ──────────────────────────────────────────────
    # Test 7: License metadata (non-null)
    # ──────────────────────────────────────────────
    cur.execute("SELECT COUNT(*) FROM reference_images WHERE license IS NOT NULL AND license != '';")
    license_count = cur.fetchone()[0]
    results.append(TestResult(
        "License metadata",
        license_count == total_images,
        f"{license_count}/{total_images} images have license",
        f"= {total_images} (100%)",
        str(license_count),
    ))
    
    # ──────────────────────────────────────────────
    # Test 8: No NULLs in required fields
    # ──────────────────────────────────────────────
    cur.execute("""
        SELECT COUNT(*) FROM reference_images 
        WHERE source IS NULL 
           OR source_url IS NULL 
           OR storage_path IS NULL 
           OR room_type IS NULL 
           OR style_tags IS NULL;
    """)
    null_count = cur.fetchone()[0]
    results.append(TestResult(
        "No NULLs in required fields",
        null_count == 0,
        f"{null_count} rows with NULL in required fields",
        "0",
        str(null_count),
    ))
    
    # ──────────────────────────────────────────────
    # Test 9: FTS retrieval returns rows when catalog is populated
    # ──────────────────────────────────────────────
    if has_fts_rpc and total_images > 0:
        cur.execute(
            "SELECT COUNT(*) FROM retrieve_candidates_text(%s, NULL, NULL, 5) AS t;",
            ("interior",),
        )
        fts_rows = cur.fetchone()[0]
        results.append(TestResult(
            "FTS retrieve_candidates_text smoke",
            fts_rows >= 1,
            f"retrieve_candidates_text('interior', ...) returned {fts_rows} row(s)",
            ">= 1 row",
            str(fts_rows),
        ))
    else:
        results.append(TestResult(
            "FTS retrieve_candidates_text smoke",
            False,
            "Skipped: RPC missing or empty catalog",
            "RPC + images",
            "skipped",
        ))
    
    cur.close()
    conn.close()
    
    return results


def print_report(results):
    """Print formatted test report."""
    print("\n" + "=" * 70)
    print("  SEED VERIFICATION REPORT")
    print("=" * 70)
    
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        marker = "[+]" if r.passed else "[-]"
        print(f"\n  {marker} {r.name}: {status}")
        print(f"      Expected: {r.expected}")
        print(f"      Actual:   {r.actual}")
        if r.details:
            print(f"      Details:  {r.details}")
    
    print("\n" + "-" * 70)
    print(f"  Results: {passed} passed, {failed} failed, {len(results)} total")
    
    if failed == 0:
        print("  STATUS: ALL TESTS PASSED")
    else:
        print("  STATUS: SOME TESTS FAILED")
    print("=" * 70 + "\n")
    
    return failed == 0


def main():
    print("\nConnecting to database...")
    try:
        results = run_tests()
        all_passed = print_report(results)
        sys.exit(0 if all_passed else 1)
    except Exception as e:
        print(f"\nERROR: Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
