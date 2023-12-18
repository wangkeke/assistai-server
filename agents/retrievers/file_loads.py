from typing import Tuple, List
from langchain.document_loaders import TextLoader, PyPDFium2Loader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

def doc_loads(
        file_path: str, 
        file_etag: str, 
        id_key: str
        ) -> Tuple[List[str], List[Document], List[Document]]:
    if not file_etag:
        file_etag = file_path
    if not id_key:
        id_key = "doc_id"
    if file_path.endswith((".txt",".sql",".log",".mq4",".mq5",".mqh")):
        docs, large_docs = text_load(file_path)
    elif file_path.endswith((".pdf")):
        docs, large_docs = pdf_load(file_path)
    text_splitter = RecursiveCharacterTextSplitter()
    docs = text_splitter.split_documents(docs)
    import uuid
    doc_ids = [str(uuid.uuid4()) for _ in docs]
    for i, doc in enumerate(docs):
        doc.metadata[id_key] = doc_ids[i]
        doc.metadata["file_etag"] = file_etag
    
    return doc_ids, docs, large_docs
    

    # ".doc",".docx",".xls",".xlsx",".ppt",".pptx",".csv",".pdf",
    # ".json",".md",".html",".htm",".ipynb",
    # ".java",".py",".js",".jsx",".ts",".tsx",".vue",".rtf",".bat",
    # ".css",".cs",".php",".c",".cpp",".swift",".go",".scala",".dart",".lua",".sh",".bash",
    # ".ini",".config",".yaml",".yml",
def text_load(file_path: str) -> Tuple[List[Document], List[Document]]:
    """load file data, Included file format: .txt, .log, .sql"""
    data = TextLoader(file_path=file_path, encoding="utf-8").load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0)
    docs = text_splitter.split_documents(data)
    large_text_splitter = RecursiveCharacterTextSplitter(chunk_size=5000)
    large_docs = large_text_splitter.split_documents(data)
    return docs, large_docs

def pdf_load(file_path: str) -> Tuple[List[Document], List[Document]]:
    """load file data, Included file format: .pdf"""
    docs = PyPDFium2Loader(file_path=file_path, extract_images=True).load()
    full_docs = [doc.page_content for doc in docs]
    full_document = Document(page_content="\n\n".join(full_docs), metadata={"source": file_path})
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=5000)
    large_docs = text_splitter.split_documents([full_document])
    return docs, large_docs 
