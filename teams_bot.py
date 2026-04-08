from botbuilder.core import ActivityHandler, TurnContext, MessageFactory
from botbuilder.schema import Activity
from botframework.connector.auth import MicrosoftAppCredentials
from aiohttp import web
from botbuilder.integration.aiohttp import CloudAdapter, ConfigurationBotFrameworkAuthentication
from botbuilder.core.integration import aiohttp_error_middleware
import asyncio
from agent import ask, ingest_mode_teams
from knowledge_base import get_stats
from config import APP_ID, APP_PASSWORD

# Each user gets their own memory and mode
# so multiple employees can use the bot simultaneously
user_sessions = {}

def get_session(user_id: str) -> dict:
    """Get or create a session for a user."""
    if user_id not in user_sessions:
        from agent import ShortTermMemory
        user_sessions[user_id] = {
            "memory": ShortTermMemory(max_turns=10),
            "mode":   "query",
            "ingest_buffer": []  # holds content during ingest flow
        }
    return user_sessions[user_id]

class ConsultantBot(ActivityHandler):

    async def on_message_activity(self, turn_context: TurnContext):
        user_id  = turn_context.activity.from_property.id
        text     = turn_context.activity.text.strip()
        session  = get_session(user_id)
        mode     = session["mode"]
        memory   = session["memory"]

        # ── Commands ──────────────────────────────
        if text.lower() == "/ingest":
            session["mode"] = "ingest"
            session["ingest_buffer"] = []
            await turn_context.send_activity(
                "📥 **Ingest mode activated.**\n\nPaste the content you want to save, then type `/done` when finished."
            )
            return

        if text.lower() == "/query":
            session["mode"] = "query"
            session["ingest_buffer"] = []
            await turn_context.send_activity("🔍 **Switched to query mode.** Ask me anything!")
            return

        if text.lower() == "/stats":
            stats = get_stats()
            await turn_context.send_activity(
                f"📊 **Knowledge base:** {stats['total_chunks']} chunks\n"
                f"🧠 **Memory:** {memory.stats()}"
            )
            return

        if text.lower() == "/clear":
            memory.clear()
            await turn_context.send_activity("🗑️ Memory cleared!")
            return

        if text.lower() == "/help":
            await turn_context.send_activity(
                "**Available commands:**\n\n"
                "`/ingest` → add new data to the knowledge base\n"
                "`/query`  → ask questions (default mode)\n"
                "`/stats`  → show knowledge base and memory stats\n"
                "`/clear`  → clear your conversation memory\n"
                "`/help`   → show this message"
            )
            return

        # ── Ingest Mode Flow ───────────────────────
        if mode == "ingest":
            await self._handle_ingest(turn_context, session, text)
            return

        # ── Query Mode ─────────────────────────────
        await turn_context.send_activity("🔍 Searching company documents...")
        answer = ask(text, memory)
        await turn_context.send_activity(answer)

    async def _handle_ingest(self, turn_context: TurnContext, session: dict, text: str):
        """Multi-step ingest flow within Teams conversation."""
        buffer = session["ingest_buffer"]
        step   = len(buffer)

        # Step 0 — collecting content
        if "content" not in session:
            if text.lower() == "/done":
                if not buffer:
                    await turn_context.send_activity("⚠️ No content received. Please paste your content first.")
                    return
                session["content"] = "\n".join(buffer)
                await turn_context.send_activity(
                    f"📋 Content received ({len(session['content'].split())} words).\n\n"
                    f"What would you like to name this document?"
                )
            else:
                buffer.append(text)
                await turn_context.send_activity("✅ Content received. Keep pasting or type `/done` when finished.")
            return

        # Step 1 — collecting document name
        if "doc_name" not in session:
            session["doc_name"] = text if text else "manual_entry"
            content  = session["content"]
            doc_name = session["doc_name"]
            await turn_context.send_activity(
                f"⚠️ **About to save:**\n\n"
                f"**Name:** {doc_name}\n"
                f"**Preview:** {content[:150]}{'...' if len(content) > 150 else ''}\n\n"
                f"Type `confirm` to save or `cancel` to abort."
            )
            return

        # Step 2 — confirmation
        if text.lower() == "confirm":
            from knowledge_base import index_documents
            index_documents([{
                "name": session["doc_name"],
                "text": session["content"]
            }])
            await turn_context.send_activity(f"✅ **'{session['doc_name']}'** saved to knowledge base!")
            # Reset ingest state
            session["mode"]         = "query"
            session["ingest_buffer"] = []
            del session["content"]
            del session["doc_name"]

        elif text.lower() == "cancel":
            await turn_context.send_activity("❌ Ingestion cancelled. Nothing was saved.")
            session["mode"]         = "query"
            session["ingest_buffer"] = []
            if "content"  in session: del session["content"]
            if "doc_name" in session: del session["doc_name"]
        else:
            await turn_context.send_activity("Please type `confirm` to save or `cancel` to abort.")


# ── Web Server Setup ───────────────────────────────────────
class BotConfig:
    APP_ID       = APP_ID
    APP_PASSWORD = APP_PASSWORD

adapter = CloudAdapter(ConfigurationBotFrameworkAuthentication(BotConfig()))
bot     = ConsultantBot()

async def messages(req: web.Request) -> web.Response:
    return await adapter.process(req, bot)

app = web.Application(middlewares=[aiohttp_error_middleware])
app.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=3978)
