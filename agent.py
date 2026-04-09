import anthropic
from knowledge_base import search, get_stats, index_documents
from teams_notifier import notify_question_and_answer, WEBHOOK_URL

client = anthropic.Anthropic()

MODEL = "claude-sonnet-4-20250514"

SYSTEM_PROMPT = """
You are a helpful Consultant Agent for Shinwootns, a small cloud security company based in South Korea.

You answer questions strictly based on the company documents provided to you.
These documents represent the official knowledge base of the organization.

Rules:
- Only answer based on the document context provided to you
- Always cite which document your answer came from using [Source: filename]
- If the answer is not in the provided documents, say:
  "I couldn't find this information in the company documents.
   Please check with the relevant department directly."
- Never make up or infer information not explicitly in the documents
- Be concise, professional, and helpful
- If asked about something sensitive (salary, personal data), decline politely
"""

def build_context(chunks: list) -> str:
    if not chunks:
        return "No relevant documents found in the knowledge base."

    context = "Relevant information retrieved from company documents:\n\n"
    for i, chunk in enumerate(chunks, 1):
        context += f"[{i}] Source: {chunk['source']}\n"
        context += f"{chunk['content']}\n\n"
    return context.strip()

def ask(question: str, conversation_history: list = None) -> tuple:
    if conversation_history is None:
        conversation_history = []

    print("  🔍 Searching company documents...")
    chunks  = search(question, n_results=5)
    context = build_context(chunks)

    if chunks:
        sources = list(set(c["source"] for c in chunks))
        print(f"  📄 Found in: {', '.join(sources)}")
    else:
        sources = []
        print("  ⚠️  No relevant documents found")

    user_message = f"""Question: {question}

---
{context}
---

Please answer the question based only on the document context above.
Cite your sources."""

    messages = conversation_history + [
        {"role": "user", "content": user_message}
    ]

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages
    )

    answer = response.content[0].text

    # ── Send to Teams ──────────────────────────────────────────────────────────
    if WEBHOOK_URL:
        sent = notify_question_and_answer(question, answer, sources)
        if sent:
            print("  📨 Teams 전송 완료")

    # Save clean version to history (without injected context)
    updated_history = conversation_history + [
        {"role": "user",      "content": question},
        {"role": "assistant", "content": answer}
    ]

    return answer, updated_history

def ingest_mode():
    """Handle data ingestion into ChromaDB with user confirmation."""
    print("\n📥 INGEST MODE")
    print("Type the content you want to save to the knowledge base.")
    print("Type 'cancel' at any time to go back to query mode.\n")

    print("Content (paste your text, then press Enter twice when done):")
    lines = []
    while True:
        line = input()
        if line.lower() == "cancel":
            print("❌ Ingestion cancelled.\n")
            return
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)

    content = "\n".join(lines).strip()
    if not content:
        print("⚠️  No content entered. Returning to query mode.\n")
        return

    print("\n📋 Please provide some details about this content:")
    doc_name = input("   Document name (e.g. 'IT Policy Update'): ").strip()
    if doc_name.lower() == "cancel":
        print("❌ Ingestion cancelled.\n")
        return
    if not doc_name:
        doc_name = "manual_entry"

    print(f"\n⚠️  About to save to knowledge base:")
    print(f"   Document name  : {doc_name}")
    print(f"   Content preview: {content[:150]}{'...' if len(content) > 150 else ''}")
    print(f"   Total length   : {len(content.split())} words")

    confirm = input("\n   Save this? (yes/no): ").strip().lower()

    if confirm == "yes":
        index_documents([{
            "name": doc_name,
            "text": content
        }])
        print(f"✅ '{doc_name}' saved to knowledge base!\n")
    else:
        print("❌ Ingestion cancelled. Nothing was saved.\n")

def chat_loop():
    stats = get_stats()

    print("\n" + "=" * 60)
    print("🤝  CONSULTANT AGENT (Claude)")
    print("=" * 60)

    if stats["total_chunks"] == 0:
        print("⚠️  Knowledge base is empty!")
        print("   Run: python sync_and_learn.py first\n")
        return

    print(f"📚 Knowledge base: {stats['total_chunks']} chunks loaded")
    print(f"🤖 Model: {MODEL}")
    print(f"📨 Teams: {'연결됨 ✅' if WEBHOOK_URL else '미설정 (TEAMS_WEBHOOK_URL 없음)'}")
    print("\nCommands:")
    print("  'ingest' → switch to ingest mode to add new data")
    print("  'query'  → switch back to query mode (default)")
    print("  'stats'  → show knowledge base stats")
    print("  'exit'   → quit\n")

    history = []
    mode    = "query"

    while True:
        try:
            user_input = input(f"[{mode.upper()}] You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Goodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() == "exit":
            print("👋 Goodbye!")
            break

        if user_input.lower() == "quit":
            print("👋 Goodbye!")
            break

        if user_input.lower() == "ingest":
            mode = "ingest"
            print(f"\n📥 Switched to INGEST mode.\n")
            continue

        if user_input.lower() == "query":
            mode = "query"
            print(f"\n🔍 Switched to QUERY mode.\n")
            continue

        if user_input.lower() == "stats":
            stats = get_stats()
            print(f"\n📊 Knowledge base: {stats['total_chunks']} chunks\n")
            continue

        if mode == "ingest":
            ingest_mode()

        elif mode == "query":
            print()
            answer, history = ask(user_input, history)
            print(f"\n🤝 Consultant: {answer}\n")
            print("-" * 60)

if __name__ == "__main__":
    chat_loop()
