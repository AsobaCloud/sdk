"""Example usage of Energy Analyst RAG client."""

from ona_platform import OnaClient


def main():
    # Initialize client
    client = OnaClient(
        energy_analyst_url="http://localhost:8000"  # Or set ENERGY_ANALYST_URL env var
    )

    # Example 1: Query energy policies
    print("=== Query Energy Policies ===")
    result = client.energy_analyst.query(
        question="What are the grid code compliance requirements for solar installations in South Africa?",
        n_results=3,
    )
    print(f"Question: {result.get('question', 'N/A')}")
    print(f"\nAnswer:\n{result['answer']}")
    print(f"\nCitation: {result['citation']}")
    print(f"Model: {result['model_id']}")

    # Example 2: Upload policy documents
    print("\n=== Upload Policy Documents ===")
    upload_result = client.energy_analyst.upload_pdfs(
        ["/path/to/policy1.pdf", "/path/to/policy2.pdf"]
    )
    print(f"Files processed: {upload_result['files_processed']}")
    print(f"Documents added: {upload_result['documents_added']}")
    for detail in upload_result["details"]:
        print(f"  - {detail['filename']}: {detail['status']}")

    # Example 3: Add text documents
    print("\n=== Add Text Documents ===")
    add_result = client.energy_analyst.add_documents(
        texts=[
            "NRS 097-2-1 defines the requirements for embedded generation...",
            "The grid connection process requires compliance with...",
        ],
        metadatas=[
            {"source": "NRS 097-2-1", "document_title": "NRS 097-2-1 Grid Connection Code"},
            {"source": "Grid Guide", "document_title": "Grid Connection Process Guide"},
        ],
    )
    print(f"Documents added: {add_result['count']}")

    # Example 4: Check service health
    print("\n=== Service Health ===")
    health = client.energy_analyst.health()
    print(f"Status: {health['status']}")
    print(f"Model: {health['model_id']}")
    print(f"Document count: {health['document_count']}")

    # Example 5: Get collection info
    print("\n=== Collection Info ===")
    info = client.energy_analyst.get_collection_info()
    print(f"Collection: {info['name']}")
    print(f"Documents: {info['count']}")
    print(f"Storage: {info['storage_mb']} MB")


if __name__ == "__main__":
    main()
