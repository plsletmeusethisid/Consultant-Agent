Custom Consultant Agent for Shinwootns.
Answers employees' questions based on company data and documents.
To test:
  1. Replace the contents of company_data.txt
  2. Start the virtual environment: .\venv\Scripts\Activate.ps1
  3. Insert API key: $env:ANTHROPIC_API_KEY="your_api_key_here"
  4. Run: python sync_and_learn.py
  5. Run: python agent.py
What to expect:
  ============================================================
  🤝  CONSULTANT AGENT (Claude)
  ============================================================
  📚 Knowledge base: X chunks loaded
  🤖 Model: claude-sonnet-4-20250514
  📨 Teams: 미설정 (TEAMS_WEBHOOK_URL 없음)
  
  Commands:
    'ingest' → switch to ingest mode to add new data
    'query'  → switch back to query mode (default)
    'stats'  → show knowledge base stats
    'exit'   → quit
Enter commands and ask questions.
