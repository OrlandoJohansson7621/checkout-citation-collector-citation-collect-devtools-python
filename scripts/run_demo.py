import os
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.citation_service import CitationRequest, InfraiBoundary, collect


def main() -> None:
    query = " ".join(sys.argv[1:]).strip() or "checkout release API diagnostics"
    boundary = InfraiBoundary()
    request = CitationRequest(
        query=query,
        max_results=5,
        archive_bucket=os.environ.get("ARCHIVE_BUCKET", ""),
    )
    citations = collect(request, boundary)
    for citation in citations:
        print(f"{citation.title}: {citation.url}")
    print(f"Collected {len(citations)} distinct citations.")


if __name__ == "__main__":
    main()
