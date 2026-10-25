from src.citation_service import dedupe_citations


def test_dedupe_keeps_the_longest_note_for_a_repeated_source():
    rows = [
        {"title": "Short release note", "url": "https://docs.example.dev/release#api", "text": "short"},
        {"title": "Full release note", "url": "https://docs.example.dev/release", "text": "longer checkout API detail"},
        {"title": "Separate guide", "url": "https://docs.example.dev/guide", "text": "cart diagnostics"},
    ]

    result = dedupe_citations(rows)

    assert len(result) == 2
    assert {row["title"] for row in result} == {"Full release note", "Separate guide"}

