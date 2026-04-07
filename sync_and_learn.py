from knowledge_base import index_documents, get_stats
from config import DATA_FILE_PATH

def main():
    print("=" * 60)
    print("📚 CONSULTANT AGENT — KNOWLEDGE BASE BUILDER")
    print("=" * 60)

    # Read the local text file
    print(f"\n📄 Reading: {DATA_FILE_PATH}")
    try:
        with open(DATA_FILE_PATH, "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        print(f"\n❌ File not found: {DATA_FILE_PATH}")
        print("   Make sure company_data.txt exists in this folder.")
        return

    if not text.strip():
        print("\n❌ File is empty.")
        return

    docs = [{"name": "company_data.txt", "text": text}]

    # Index into vector database
    print("\n🧠 Building knowledge base...")
    index_documents(docs)

    # Confirm
    stats = get_stats()
    print(f"\n✅ Knowledge base ready!")
    print(f"   Chunks indexed: {stats['total_chunks']}")
    print(f"\n▶  Now run: python agent.py")

if __name__ == "__main__":
    main()