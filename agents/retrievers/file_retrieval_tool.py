__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
from typing import Tuple
from langchain.storage import LocalFileStore
from langchain.vectorstores.chroma import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain.retrievers.multi_vector import MultiVectorRetriever
from agents.core import chat_open_ai, chat_open_ai_16k, embeddings
from agents.retrievers.file_loads import doc_loads


async def summary_of_files(user_id: int, user_partition: str, content: str, tool_args: dict):
    """Useful when you need to retrieve summaries of uploaded files, excluding image files."""
    file_urls: list[str] = tool_args.get("file_urls")
    summaries = []
    retriever: MultiVectorRetriever = get_retriever(user_partition=user_partition, search_type="mmr", search_kwargs={"k":1})
    for i, file_url in enumerate(file_urls):
        final_path_pos = file_url.rfind("/")
        file_name = file_url[final_path_pos+1:]
        file_etag = file_name[:file_name.rfind(".")]
        summary_document: Document = parse_file(retriever=retriever, 
                                                file_name=file_name, 
                                                file_etag=file_etag, 
                                                user_partition=user_partition)
        summaries.append(f"{i+1}: {summary_document.page_content}")
    return "Here is the results from the summary_of_files tool: \n\n" + ("\n".join(summaries))


async def retrieval_of_files(user_id: int, user_partition: str, content: str, tool_args: dict):
    """Useful when you need to retrieve documents relevant to a query, excluding image files."""
    file_urls: list[str] = tool_args.get("file_urls")
    query: str = tool_args.get("query")
    page: int = tool_args.get("page", None)
    retriever: MultiVectorRetriever = get_retriever(user_partition=user_partition, search_type="mmr", search_kwargs={"k":1})
    relevant_documents = []
    for file_url in file_urls:
        final_path_pos = file_url.rfind("/")
        file_name = file_url[final_path_pos+1:]
        file_etag = file_name[:file_name.rfind(".")]
        full_summary_document = parse_file(retriever=retriever, file_name=file_name, file_etag=file_etag, user_partition=user_partition)
        metadata={"source": file_name}
        total_pages: int = full_summary_document.metadata["total_pages"]
        if page:
            metadata["page"] = total_pages + page - 1
        relevant_documents.extend(retriever.get_relevant_documents(query=query, metadata=metadata))
    results = []
    for i, relevant_document in enumerate(relevant_documents):
        results.append(f"{i+1}: " + relevant_document.page_content)
    return "Here is the result from the retrieval_of_files tool:\n\n" + ("\n".join(results))    


def parse_file(retriever: MultiVectorRetriever, file_name: str, file_etag: str, user_partition: str) -> Document:
    """parse uploaded file"""
    summary_document = retriever.docstore.mget([file_etag])[0]
    if summary_document:
        return summary_document
    summary_chain = (
        {"doc": lambda x: x.page_content}
        | ChatPromptTemplate.from_template("Summarize the following document in less than 200 words:\n\n{doc}")
        | chat_open_ai
        | StrOutputParser()
    )
    doc_ids, docs, large_docs = doc_loads(user_partition + "/upload/" + file_name, file_etag=file_etag, id_key=retriever.id_key)
    total_pages = len(docs)
    fragment_summaries = summary_chain.batch(large_docs, {"max_concurrency": 5})
    full_summary_chain = (
        {"content": lambda contents: "\n\n".join(contents)}
        | ChatPromptTemplate.from_template("Summarize the following document:\n\n{content}")
        | chat_open_ai_16k
        | StrOutputParser()
    )
    full_summary_text = full_summary_chain.invoke(fragment_summaries)
    full_summary_document = Document(page_content=full_summary_text, 
                                        metadata={"source": file_name, "doc_id": file_etag, "total_pages": total_pages})
    retriever.vectorstore.add_documents(docs)
    retriever.docstore.mset(list(zip(doc_ids, docs)))
    retriever.docstore.mset([(file_etag, full_summary_document)])
    return full_summary_document


def get_retriever(user_partition: str, search_type: str, search_kwargs: dict):
    # The storage layer for the parent documents
    docstore = LocalFileStore(f"{user_partition}/store/docs")
    bytestore = LocalFileStore(f"{user_partition}/store/bytes")
    id_key = "doc_id"
    # The vectorstore to use to index the child chunks
    vectorstore = Chroma(collection_name="documents", 
                         persist_directory=f"{user_partition}/chromadb/collections", 
                         embedding_function=embeddings)
    return MultiVectorRetriever(
        vectorstore=vectorstore,
        byte_store=bytestore,
        docstore=docstore,
        id_key=id_key,
        search_type=search_type,
        search_kwargs=search_kwargs,
    )