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
    for i, file_url in enumerate(file_urls):
        final_path_pos = file_url.rfind("/")
        file_name = file_url[final_path_pos+1:]
        file_etag = file_name[:file_name.rfind(".")]
        summary = parse_file(file_name=file_name, 
                             file_etag=file_etag, 
                             user_partition=user_partition)
        summaries.append(f"{i+1}: " + summary.page_content)
    result = "\n".join(summaries)
    return f"Here is the result from the summary_of_files tool: {result}"


async def retrieval_of_files(user_id: int, user_partition: str, content: str, tool_args: dict):
    """Useful when you need to retrieve documents relevant to a query, excluding image files."""
    file_urls: list[str] = tool_args.get("file_urls")
    query: str = tool_args.get("query")
    page: int = tool_args.get("page", None)
    # The storage layer for the parent documents
    docstore = LocalFileStore(f"{user_partition}/store/docs")
    bytestore = LocalFileStore(f"{user_partition}/store/bytes")
    id_key = "doc_id"
    # The vectorstore to use to index the child chunks
    vectorstore = Chroma(collection_name="documents", 
                         persist_directory=f"{user_partition}/chromadb/collections", 
                         embedding_function=embeddings)
        # The retriever (empty to start)
    retriever = MultiVectorRetriever(
        vectorstore=vectorstore,
        byte_store=bytestore,
        docstore=docstore,
        id_key=id_key,
        search_type="mmr",
        search_kwargs={
            "k": 1
        },
    )
    relevant_documents = []
    for file_url in file_urls:
        final_path_pos = file_url.rfind("/")
        file_name = file_url[final_path_pos+1:]
        file_etag = file_name[:file_name.rfind(".")]
        parse_file(file_name=file_name, file_etag=file_etag, user_partition=user_partition)
        metadata={"source": file_name}
        if page:
            metadata["page"] = page+1
        relevant_documents.extend(retriever.get_relevant_documents(query=query, metadata=metadata))
    results = []
    for i, relevant_document in enumerate(relevant_documents):
        results.append(f"{i+1}: " + relevant_document.page_content)
    result = "\n".join(results)
    return f"Here is the result from the retrieval_of_files tool: {result}"
    

def parse_file(file_name: str, file_etag: str, user_partition: str) -> Document:
    """parse uploaded file"""
    # The storage layer for the parent documents
    docstore = LocalFileStore(f"{user_partition}/store/docs")
    summary = docstore.mget([file_etag])
    if summary:
        return summary[0]
    # The vectorstore to use to index the child chunks
    vectorstore = Chroma(collection_name="documents", 
                         persist_directory=f"{user_partition}/chromadb/collections", 
                         embedding_function=embeddings)
    id_key = "doc_id"
    summary_chain = (
        {"doc": lambda x: x.page_content}
        | ChatPromptTemplate.from_template("Summarize the following document in less than 200 words:\n\n{doc}")
        | chat_open_ai
        | StrOutputParser()
    )
    doc_ids, docs, large_docs = doc_loads(user_partition + "/upload/" + file_name, file_etag=file_etag, id_key=id_key)
    fragment_summaries = summary_chain.batch(large_docs, {"max_concurrency": 5})
    full_summary_chain = (
        {"content": lambda contents: "\n\n".join(contents)}
        | ChatPromptTemplate.from_template("Summarize the following document:\n\n{content}")
        | chat_open_ai_16k
        | StrOutputParser()
    )
    full_summary_text = full_summary_chain.invoke(fragment_summaries)
    full_summary_document = Document(page_content=full_summary_text, 
                                        metadata={"source": file_name, "doc_id": file_etag})
    docs.append(full_summary_document)
    doc_ids.append(file_etag)
    vectorstore.add_documents(docs)
    docstore.mset(list(zip(doc_ids, docs)))
    return full_summary_document