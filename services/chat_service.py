"""AI Chat Service — RAG chatbot with dynamic context retrieval and citation generator."""
from __future__ import annotations

import json
import re
from typing import Optional, Any
import urllib.request
import urllib.error

from database.db_manager import DatabaseManager
from services.search_service import SearchService, SearchResult


class ChatService:
    """Orchestrates search-based Retrieval-Augmented Generation (RAG) chat."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self._db = db or DatabaseManager()
        self._search_service = SearchService(self._db)

    def ask(
        self,
        message: str,
        chat_history: list[dict],
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
    ) -> dict[str, Any]:
        """
        Ask the AI chatbot a question.

        Args:
            message: The user's question.
            chat_history: List of past messages (dict with 'role' and 'content').
            api_key: Optional OpenAI API key.
            model: Model to use if key is provided.

        Returns:
            Dict containing 'response' (markdown string) and 'citations' (list of dicts).
        """
        # 1. Retrieve relevant contexts using SearchService
        search_results = self._search_service.search(message, exact_phrase=False)
        
        # Keep top 5 unique document chunks/pages
        citations: list[dict] = []
        contexts: list[str] = []
        seen_chunks = set()

        for res in search_results[:8]:
            doc_id = res.doc_id
            filename = res.filename
            file_type = res.file_type
            
            # Format location string
            if res.page_number:
                loc = f"Page {res.page_number}"
            elif res.sheet_name and res.cell_ref:
                loc = f"Sheet: {res.sheet_name}, Cell: {res.cell_ref}"
            else:
                loc = "Full Document"

            chunk_key = (doc_id, loc)
            if chunk_key in seen_chunks:
                continue
            seen_chunks.add(chunk_key)

            # Record citation
            citations.append({
                "doc_id": doc_id,
                "filename": filename,
                "file_type": file_type,
                "location": loc,
                "snippet": res.snippet
            })

            # Retrieve full text context for RAG prompt
            full_text = self._db.get_extracted_text(doc_id)
            if res.page_number and file_type == ".pdf":
                # Split pages and get the specific page content
                pages = full_text.split("\f")
                if 0 < res.page_number <= len(pages):
                    page_content = pages[res.page_number - 1].strip()
                    contexts.append(f"[Source: {filename}, Location: {loc}]\n{page_content}")
            elif file_type in (".xlsx", ".xls") and res.sheet_name:
                # Find matching spreadsheet rows
                matching_rows = []
                for line in full_text.split("\n"):
                    if line.startswith(f"{res.sheet_name}\t"):
                        parts = line.split("\t", 2)
                        if len(parts) == 3:
                            matching_rows.append(f"[{parts[1]}] {parts[2]}")
                contexts.append(f"[Source: {filename}, Location: {loc}]\n" + "\n".join(matching_rows[:20]))
            else:
                # Text / Word / Default: take snippet surrounding region or first 2000 chars
                contexts.append(f"[Source: {filename}, Location: {loc}]\n{res.snippet}")

        # Limit aggregated context size
        aggregated_context = "\n\n".join(contexts[:4])

        # 2. Call OpenAI if API key exists, otherwise local fallback
        if api_key and api_key.strip().startswith("sk-"):
            try:
                response_text = self._call_openai_api(message, chat_history, aggregated_context, api_key, model)
                self._db.add_chat_history(message, response_text, json.dumps(citations))
                return {"response": response_text, "citations": citations}
            except Exception as exc:
                # Return error but fallback to local parser for robustness
                response_text = f"*(OpenAI API call failed: {exc}. Falling back to offline answer engine)*\n\n"
                local_answer = self._generate_local_response(message, citations)
                response_text += local_answer
                self._db.add_chat_history(message, response_text, json.dumps(citations))
                return {"response": response_text, "citations": citations}
        else:
            response_text = self._generate_local_response(message, citations)
            self._db.add_chat_history(message, response_text, json.dumps(citations))
            return {"response": response_text, "citations": citations}

    def _call_openai_api(
        self,
        message: str,
        chat_history: list[dict],
        context: str,
        api_key: str,
        model: str
    ) -> str:
        """Call OpenAI chat completion endpoint using Python standard library."""
        url = "https://api.openai.com/v1/chat/completions"
        
        # Build messages payload
        system_instruction = (
            "You are DocMind AI, a helpful research assistant. "
            "You help users analyze documents in their library. "
            "Use the provided context chunks below to answer the user's question. "
            "If the information is not in the context, say that you don't know based on the documents. "
            "Always cite the source document names when referencing information.\n\n"
            f"--- DOCUMENT CONTEXT CHUNKS ---\n{context}"
        )
        
        messages = [{"role": "system", "content": system_instruction}]
        
        # Include conversation history (limit to last 10 messages)
        for turn in chat_history[-10:]:
            messages.append({"role": turn["role"], "content": turn["content"]})
            
        messages.append({"role": "user", "content": message})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 1000
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=30) as res:
            res_body = json.loads(res.read().decode("utf-8"))
            return res_body["choices"][0]["message"]["content"]

    def _generate_local_response(self, message: str, citations: list[dict]) -> str:
        """Fallback local response generator using document search snippets."""
        if not citations:
            return (
                "I couldn't find any documents in your library matching that query. "
                "Please make sure your search terms are present in your papers, or try uploading "
                "additional research documents in the **Upload** tab."
            )

        # Keyword mapping matching the question
        summary_blocks = []
        for i, cit in enumerate(citations[:3], 1):
            clean_snippet = re.sub(r'\s+', ' ', cit['snippet']).strip()
            summary_blocks.append(
                f"- **{cit['filename']}** ({cit['location']}):\n"
                f"  > *\"{clean_snippet}\"*"
            )

        sources_list = ", ".join([f"`{c['filename']}`" for c in citations[:4]])
        
        response = (
            f"### Document Intelligence Insights\n\n"
            f"I found {len(citations)} relevant matches in your library. Here is what they contain:\n\n"
            + "\n".join(summary_blocks) + "\n\n"
            f"**Citations:**\n"
            f"The details above were extracted from: {sources_list}.\n\n"
            f"*(To enable advanced AI reasoning, configure an OpenAI API key in the **Settings** tab)*"
        )
        return response
