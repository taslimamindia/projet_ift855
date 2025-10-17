from typing import List

from langchain.llms.base import LLM
from langchain.chains import RetrievalQA
from langchain.schema import BaseRetriever, Document
from langchain.prompts import PromptTemplate

from .LLM import Fireworks_LLM
from .faissmanager import Faiss
from outils.dataset import Data


class FireworksLangChain(LLM):
    """Adapter to use Fireworks_LLM with LangChain's LLM interface."""

    fw_llm: Fireworks_LLM = None

    def _call(self, prompt: str, stop=None) -> str:
        try:
            result = self.fw_llm.generate_QA(prompt=prompt)
            if result is None:
                return ""
            return str(result)
        except Exception as e:
            # re-raise to let upstream handle logging
            raise

    @property
    def _identifying_params(self):
        return {"model": getattr(self.fw_llm, "data", None)}

    @property
    def _llm_type(self):
        return "fireworks"


class FaissRetriever(BaseRetriever):
    """Simple LangChain-style retriever backed by the project's Faiss implementation."""

    faiss: Faiss = None
    data: Data = None
    k: int = 5

    def get_relevant_documents(self, query: str) -> List[Document]:
        urls = self.faiss.search_similar_documents(query, k=self.k)
        docs: List[Document] = []

        for url in urls:
            content = self.data.documents.get(url, "")
            docs.append(Document(page_content=content, metadata={"source": url}))

        return docs


class LangChainRAGAgent:
    """High-level RAG agent using LangChain's RetrievalQA chain."""

    def __init__(self, data: Data, faiss: Faiss, fw_llm: Fireworks_LLM):
        self.data = data
        self.faiss = faiss
        self.fw_llm = fw_llm
        self.prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template=(
                "You are a helpful assistant. Use only the information below to answer the user’s question.\n\n"
                "Context:\n{context}\n\n"
                "Question: {question}\n\n"
                "Answer (Please provide a clear, concise, and precise answer):"
            )
        )


    def answer(self, query: str, k: int = 5) -> dict:
    # Build LangChain components
    # Pass fw_llm as a keyword so pydantic-based LangChain LLM accepts it
        llm = FireworksLangChain(fw_llm=self.fw_llm)
        retriever = FaissRetriever(faiss=self.faiss, data=self.data, k=k)

        # Create a RetrievalQA chain; return source documents to expose provenance
        try:
            chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True,
                chain_type_kwargs={"prompt": self.prompt_template}
            )
            result = chain.invoke({"query": query})

            answer = result.get("result") or result.get("output_text") or ""
            source_docs = result.get("source_documents", [])
            passages = []
            sources = []
            for doc in source_docs:
                if isinstance(doc.metadata, dict):
                    src = doc.metadata.get("source")
                else:
                    src = getattr(doc.metadata, "source", None)
                passages.append({"source": src, "text": doc.page_content})
                if src:
                    sources.append(src)

            return {
                "query": query,
                "response": answer,
                "sources": list(dict.fromkeys(sources)),
                "context": " \n\n ".join([p["text"] for p in passages]) if passages else "",
                "passages": passages,
            }
        
        except Exception as e:
            # Fallback simple behaviour: use earlier simple RAG flow
            print(f"LangChain RAG failed: {e}")