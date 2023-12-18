import urllib.request
import uuid
import os
from datetime import date, datetime 

# response = urllib.request.urlopen("https://cdn.openai.com/API/images/guides/image_generation_simple.webp")
# data = response.read()
# os.makedirs("/home/data/images")
# image_path = f"/images/{str(uuid.uuid4())}.webp"
# with open("/home/data" + image_path, 'wb') as f: 
#     f.write(data)
# print("写入完成")

# os.makedirs(f"/home/data/images", exist_ok=True)

print(date.today())

chunk = {"message": True}

print(list(chunk.keys())[0])

print(str(chunk.get(list(chunk.keys())[0])))

#
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

llm = ChatOpenAI(temperature=0, 
                 openai_api_key="123456789", 
                 openai_api_base="https://assistai-server.onrender.com/openai_agent")
prompt = PromptTemplate.from_template("Tell me a joke about {topic}")

chain = prompt | llm

print( chain.invoke({"topic": "bears"}) )

# 
from langchain.chat_models import ChatOpenAI, ChatAnthropic
from unittest.mock import patch
from openai.error import RateLimitError
openai_llm = ChatOpenAI(max_retries=0)
anthropic_llm = ChatAnthropic()
llm = openai_llm.with_fallbacks([anthropic_llm])
with patch("openai.ChatCompletion.create", side_effect=RateLimitError()):
    try:
        print(llm.invoke("Why did the chicken cross the road?"))
    except:
        print("Hit error")


def test():
    """这是一个测试函数"""
    print("This is test")

print(test.__name__)
print(test.__doc__)

import json
from fastapi.encoders import jsonable_encoder

json_args = json.loads("{\"location\": \"Boston, MA\", \"array\":[1,2,3]}")

def function(args: dict):
    print(args)
    print(args.get("location"))
    print(args.get("test"))

print(function(json_args))

chats = []
chats.append({"role":"user", "content": "text"})

chats_encoder = jsonable_encoder(chats)
print(chats_encoder[0].__class__)


supported_file_suffixes = (
    ".jpg",".jpeg",".png",".webp",".gif",
    ".doc",".docx",".xls",".xlsx",".ppt",".pptx",".csv",".pdf",
    ".txt",".sql",".json",".java",".py",".mq4",".mq5",".mqh",".js",".ts",".log",".html",".htm",".md",".vue"
    )
file_name = "卢新.jpg"
print(file_name.endswith(supported_file_suffixes))

filename = 'example.jpg'
ext_pos = filename.rfind('.') + 1
ext = filename[ext_pos:]
print(ext) # 'jpg'

from datetime import date, datetime


print(datetime.now().strftime("%Y%m%d%H%M%S%f"))

import hashlib

print(hashlib.md5(b"wangkeke565@163.com").hexdigest())
print(hashlib.md5(b"wangkeke565@126.com").hexdigest())
print(hashlib.md5(b"wangkeke565@qq.com").hexdigest())
print(hashlib.md5(b"wangkeke565@zenking.com").hexdigest())
print(hashlib.md5("wangkeke565@zenking.com".encode()).hexdigest())






from openai import OpenAI
import json
import logging

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY", "1234567890"),
    max_retries=0,
    base_url="http://43.153.6.89:8000/agent/openai"
    )

# Example dummy function hard coded to return the same weather
# In production, this could be your backend API or an external API
def get_current_weather(args: dict):
    """Get the current weather in a given location"""
    location = args.get("location")
    unit="fahrenheit"
    if args.get("unit"):
        unit = args.get("unit")
    if "tokyo" in location.lower():
        return json.dumps({"location": "Tokyo", "temperature": "10", "unit": "celsius"})
    elif "san francisco" in location.lower():
        return json.dumps({"location": "San Francisco", "temperature": "72", "unit": "fahrenheit"})
    elif "paris" in location.lower():
        return json.dumps({"location": "Paris", "temperature": "22", "unit": "celsius"})
    else:
        return json.dumps({"location": location, "temperature": "unknown"})

def generate_image(args: dict):
    """Generate an image based on the prompt"""
    prompt: str = args.get("prompt")
    return json.dumps({"prompt": prompt, "image_url": f'https://cdn.openai.com/API/images/guides/image_generation_simple.webp'})

def understanding_image(args: dict):
    """Understand images based on user description"""
    text: str = args.get("text")
    image_urls: list[str] = args.get("image_urls")
    return "这是一段python代码的截图：\n\n下面是一个用Python写的斐波那契函数，其参数是n：\n\n```python\n def fibonacci(n):\n    if n <= 0:\n        return []\n    elif n == 1:\n        return [0]\n    else:\n        sequence = [0, 1]\n        while len(sequence) < n:\n            next_number = sequence[-1] + sequence[-2]\n            sequence.append(next_number)\n        return sequence\n```\n\n这个函数将返回一个包含n个斐波那契数列的列表。如果n小于等于0，将返回一个空列表。如果n等于1，将返回一个只包含0的列表。否则，函数将使用循环构建斐波那契数列，直到列表达到n个元素。\n\n "

def run_conversation():
    # Step 1: send the conversation and available functions to the model
    # messages = [{"role": "user", "content": "What's the weather like in San Francisco, Tokyo, and Paris?"}]
    messages = [{"role": "user", "content": "Generate a picture of a white cat."}]
    # messages = [{"role": "user", "content": "Depending on whether a function call is required as described below, the generated message can only answer yes or no: Hello!"}]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA",
                        },
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                    },
                    "required": ["location"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": generate_image.__name__,
                "description": generate_image.__doc__,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "a detailed prompt to generate an image",
                        },
                    },
                    "required": ["prompt"],
                },
            }
        },
        {
            "type": "function",
            "function": {
                "name": understanding_image.__name__,
                "description": understanding_image.__doc__,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image_urls": {"type": "array", "items": {"type": "string"}, "description": "List of urls for images"},
                        "text": {"type": "string", "description": "Other text content"},
                    },
                    "required": ["text", "image_urls"],
                },
            }
        },
    ]
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=messages,
        tools=tools,
        tool_choice="auto",  # auto is default, but we'll be explicit
    )
    print(response)
    response_message = response.choices[0].message
    if response_message.content is None:
        response_message.content = ""
    if response_message.function_call is None:
        del response_message.function_call
    tool_calls = response_message.tool_calls
    # Step 2: check if the model wanted to call a function
    if tool_calls:
        # Step 3: call the function
        # Note: the JSON response may not always be valid; be sure to handle errors
        available_functions = {
            "get_current_weather": get_current_weather,
            "generate_image": generate_image,
            "understanding_image": understanding_image
        }  # only one function in this example, but you can have multiple
        messages.append(response_message)  # extend conversation with assistant's reply
        # Step 4: send the info for each function call and function response to the model
        print(messages)
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(function_args)
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )  # extend conversation with function response
        second_response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=messages,
        )  # get a new response from the model where it can see the function response
        return second_response
print(run_conversation())



new_messages = [{"role": "user"}]
print(new_messages[0]["role"])



import orm.schemas
import orm.models
import json
from datetime import datetime

topic_chat = orm.models.TopicChat(role="role", content_type="content_type", content="topic_chat.content", 
                                  topic_id="topic_id", 
                                  create_time=datetime.now(), 
                                  flag=True,
                                  id= 1
                                  )
print(json.dumps({"id" : topic_chat.id, "role": "assistant", "content": "dsadsada","content_type": "text", "create_time": datetime.now().isoformat(), "remain_num": 3}))






from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4-vision-preview",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What’s in this image?"},
                {
                    "type": "image_url",
                    "image_url": "https://www.uassistant.net/api/static/upload/7b8ea8096943efb4ae9c221395803ec1/29124d19-764a-4cea-844d-1bd7645ed622.jpg",
                },
            ],
        }
    ],
    max_tokens=300,
)

print(response.choices[0])

# langchain文档解析

from openai import OpenAI
import json

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY", "1234567890"),
    max_retries=0,
    base_url="http://43.153.6.89:8000/agent/openai"
    )

from langchain.document_loaders import TextLoader

loader = TextLoader("D:\\个人简历.md", encoding="utf-8")
loader.load()

from langchain.document_loaders.markdown import UnstructuredMarkdownLoader

loader = UnstructuredMarkdownLoader("D:\\个人简历.md", mode="elements")
loader.load()

from langchain.document_loaders.csv_loader import CSVLoader

loader = CSVLoader(file_path="D:\\sys_dict.csv", autodetect_encoding=True,
                   csv_args={
                       'delimiter': ',',
                       'quotechar': '"',
                       'fieldnames': ['id']
                   })
loader.load()

from langchain.document_loaders import BSHTMLLoader

loader = BSHTMLLoader(file_path="D:\\LLM Powered Autonomous Agents _ Lil'Log.html",
                      open_encoding="utf-8")
loader.load()

# ====================================================
from openai import OpenAI
from langchain.document_loaders import PyPDFLoader

# loader = PyPDFLoader(file_path="D:\\100个Python爬虫常见问题(3).pdf", 
#                      extract_images=True)
loader = PyPDFLoader(file_path="D:\\清华工程教育探究课程个人心得_20231211161930.pdf",
                     extract_images=True)
pages = loader.load_and_split()
pages[0]

from langchain.vectorstores.faiss import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings

faiss_index = FAISS.from_documents(pages, 
                                   OpenAIEmbeddings(
                                       base_url="http://43.153.6.89:8000/agent/openai",
                                       api_key="123456789",
                                   ))
docs = faiss_index.similarity_search(query="第一次课", k=4)
docs
# for doc in docs:
#     f'{doc.metadata["page"]} : {doc.page_content[:300]}'


from langchain.document_loaders import PDFPlumberLoader

loader = PDFPlumberLoader(file_path="D:\\清华工程教育探究课程个人心得_20231211161930.pdf")
data = loader.load_and_split()
data

from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    Language
)

[e.value for e in Language]

# ====================================================
from langchain.chains import LLMChain, StuffDocumentsChain
from langchain.document_transformers import (
    LongContextReorder,
)
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms.openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.vectorstores.chroma import Chroma

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2",
                                   )
texts = [
    "Basquetball is a great sport.",
    "Fly me to the moon is one of my favourite songs.",
    "The Celtics are my favourite team.",
    "This is a document about the Boston Celtics",
    "I simply love going to the movies",
    "The Boston Celtics won the game by 20 points",
    "This is just a random text.",
    "Elden Ring is one of the best games in the last 15 years.",
    "L. Kornet is one of the best Celtics players.",
    "Larry Bird was an iconic NBA player.",
]

# Create a retriever
retriever = Chroma.from_texts(texts, embedding=embeddings).as_retriever(search_kwargs={"k": 10})
query = "What can you tell me about the Celtics?"

# Get relevant documents ordered by relevance score
docs = retriever.get_relevant_documents(query)
docs

# ===================================================
from langchain.embeddings import OpenAIEmbeddings

embeddings_model = OpenAIEmbeddings(
                                       base_url="http://43.153.6.89:8000/agent/openai",
                                       api_key="123456789",
                                   )
embeddings = embeddings_model.embed_documents(
    [
        "Hi there!",
        "Oh, hello!",
        "What's your name?",
        "My friends call me World",
        "Hello World!"
    ]
)
len(embeddings), len(embeddings[0])

embedded_query = embeddings_model.embed_query("What was the name mentioned in the conversation?")
embedded_query[:5]

# ==========================================
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores.chroma import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from chromadb.config import Settings

full_text = open("state_of_the_union.txt", mode="r", encoding="utf-8").read()
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
texts = text_splitter.split_text(full_text)
embeddings = OpenAIEmbeddings(
    base_url="http://43.153.6.89:8000/agent/openai",
    api_key="1234567890"
) 
db = Chroma.from_texts(texts=texts, 
                       embedding=embeddings, 
                    #    client_settings=Settings(
                    #        is_persistent=True,
                    #        persist_directory="./chroma/user_id")
                    )
retriever = db.as_retriever()
# retrieved_docs = retriever.invoke(
#     "What did the president say about Ketanji Brown Jackson?"
# )

template = """Answer the question based only on the following context:

{context}

Question: {question}
"""
prompt = ChatPromptTemplate.from_template(template)
model = ChatOpenAI(
    base_url="http://43.153.6.89:8000/agent/openai",
    api_key="1234567890"
)


def format_docs(docs):
    return "\n\n".join([d.page_content for d in docs])


chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)

chain.invoke("What did the president say about technology?")


# ========================================================================
from langchain.vectorstores.chroma import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models.openai import ChatOpenAI

embeddings = OpenAIEmbeddings(
    base_url="http://43.153.6.89:8000/agent/openai",
    api_key="1234567890"
) 
vectorstore = Chroma(embedding_function=embeddings, persist_directory="./chroma_db_oai")
with open("state_of_the_union.txt", encoding="utf-8") as f:
    state_of_the_union = f.read()
from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=1000, chunk_overlap=0)
texts = text_splitter.split_text(state_of_the_union)
vectorstore.add_texts(texts=texts)
retriever = vectorstore.as_retriever(search_type="similarity_score_threshold", search_kwargs={"score_threshold": .5})

docs = retriever.get_relevant_documents("what did he say about ketanji brown jackson")
docs

question = "What are the approaches to Task Decomposition?"
llm = ChatOpenAI(temperature=0, 
                 base_url="http://43.153.6.89:8000/agent/openai",
                 api_key="1234567890")
from langchain.retrievers.multi_query import MultiQueryRetriever
retriever_from_llm = MultiQueryRetriever.from_llm(
    retriever=retriever, llm=llm
)
# Set logging for the queries
import logging

logging.basicConfig()
logging.getLogger("langchain.retrievers.multi_query").setLevel(logging.INFO)
unique_docs = retriever_from_llm.get_relevant_documents(query=question)
unique_docs



# =======================================================
import hashlib

hash_obj = hashlib.sha256()
with open("D:\\sys_dict.csv", "rb") as f:
    print("+++")
    hash_obj.update(f.read())
hash_obj.hexdigest()

# =========================================================
from langchain.document_loaders import TextLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.storage import InMemoryByteStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
loaders = [
    TextLoader("state_of_the_union.txt", encoding="utf-8"),
]
docs = []
for loader in loaders:
    docs.extend(loader.load())
text_splitter = RecursiveCharacterTextSplitter(chunk_size=400)
docs = text_splitter.split_documents(docs)
len(docs)

# =====================================================================
from langchain.storage import LocalFileStore, InMemoryByteStore
from langchain.document_loaders import TextLoader, PyPDFLoader, UnstructuredPDFLoader, PyPDFium2Loader
from langchain.embeddings import OpenAIEmbeddings
from langchain.storage import InMemoryByteStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain.retrievers.multi_vector import MultiVectorRetriever

# file_name = "qinghuaguanhougan.txt"
file_name = "100_Python_crawler_common_problems.pdf"

loaders = [
    PyPDFium2Loader(file_path=file_name, extract_images=True),
    # TextLoader(file_name, encoding="utf-8"),
]
docs = []
for loader in loaders:
    docs.extend(loader.load())

docs

text_splitter = RecursiveCharacterTextSplitter(chunk_size=5000)
docs = text_splitter.split_documents(docs)

docs

embeddings = OpenAIEmbeddings(
    base_url="http://43.153.6.89:8000/agent/openai",
    api_key="1234567890"
) 

chat_open_ai = ChatOpenAI(max_retries=0, 
           base_url="http://43.153.6.89:8000/agent/openai", 
           api_key="1234567890")

chat_open_ai_16k = ChatOpenAI(max_retries=0, 
           base_url="http://43.153.6.89:8000/agent/openai", 
           api_key="1234567890",
           model_name="gpt-3.5-turbo-16k")


# The vectorstore to use to index the child chunks
vectorstore = Chroma(collection_name="full_documents", persist_directory="./chromadb/collections", embedding_function=embeddings)
# The storage layer for the parent documents
# The storage layer for the parent documents
docstore = LocalFileStore("./stores/doc")
bytestore = LocalFileStore("./stores/byte")
id_key = "doc_id"
source_key = "source"
# The retriever (empty to start)
retriever = MultiVectorRetriever(
    vectorstore=vectorstore,
    byte_store=bytestore,
    docstore=docstore,
    id_key=id_key,
)
import uuid
doc_ids = [str(uuid.uuid4()) for _ in docs]

child_text_splitter = RecursiveCharacterTextSplitter(chunk_size=500)

sub_docs = []
for i, doc in enumerate(docs):
    _id = doc_ids[i]
    _sub_docs = child_text_splitter.split_documents([doc])
    for _doc in _sub_docs:
        _doc.metadata[id_key] = _id
    sub_docs.extend(_sub_docs)

retriever.vectorstore.add_documents(sub_docs)
retriever.docstore.mset(list(zip(doc_ids, docs)))

sub_docs = retriever.vectorstore.max_marginal_relevance_search("justice breyer")
sub_docs



chain = (
    {"doc": lambda x: x.page_content}
    | ChatPromptTemplate.from_template("Summarize the following document in less than 500 words:\n\n{doc}")
    | chat_open_ai_16k
    | StrOutputParser()
)

summaries = chain.batch(docs, {"max_concurrency": 5})

summary_doc_ids = [
    f"summary_{id}"
    for id in doc_ids
]

summary_docs = [
    Document(page_content=s, metadata={id_key: summary_doc_ids[i], source_key: "file_sha1_code"}) 
    for i, s in enumerate(summaries)
]
retriever.docstore.mset(list(zip(summary_doc_ids, summary_docs)))

chain = (
    {"content": lambda docs: "\n\n".join(docs)}
    | ChatPromptTemplate.from_template("Summarize the following document:\n\n{content}")
    | chat_open_ai_16k
    | StrOutputParser()
)

full_summary_text = chain.invoke(summaries)

full_summary_document = Document(page_content=full_summary_text, metadata={id_key: file_name})

retriever.docstore.mset([(file_name, full_summary_document)])

v = retriever.docstore.mget([file_name])
v


# ============================================================================
from langchain.storage import LocalFileStore, InMemoryByteStore
from langchain.document_loaders import TextLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.storage import InMemoryByteStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain.retrievers.multi_vector import MultiVectorRetriever

embeddings = OpenAIEmbeddings(
    base_url="http://43.153.6.89:8000/agent/openai",
    api_key="1234567890"
) 
# The vectorstore to use to index the child chunks
vectorstore = Chroma(collection_name="full_documents", persist_directory="./chromadb/collections", embedding_function=embeddings)
# The storage layer for the parent documents
# The storage layer for the parent documents
docstore = LocalFileStore("./stores/doc")
bytestore = LocalFileStore("./stores/byte")
id_key = "doc_id"
# The retriever (empty to start)
retriever = MultiVectorRetriever(
    vectorstore=vectorstore,
    byte_store=bytestore,
    docstore=docstore,
    id_key=id_key,
    search_type="mmr",
    search_kwargs={
        "k": 2
    },
)

sub_docs = retriever.vectorstore.max_marginal_relevance_search("justice breyer", lambda_mult=0.9)
sub_docs

retrieved_docs = retriever.get_relevant_documents("justice breyer")

retrieved_docs


# ================================================
import uuid
doc_ids = [str(uuid.uuid4()) for _ in range(5)]
summary_doc_ids = [
    f"summary_{id}"
    for id in doc_ids
]
summary_doc_ids

# ================================================

a = "a"
if a:
    b = "b"
b

tests = [{"id": 34}]
o = tests[-1]
id = o["id"]
o["id"] = id + 6
tests, id

# ========================================================

import asyncio

async def factorial(name, number):
    f = 1
    for i in range(2, number + 1):
        print(f"Task {name}: Compute factorial({number}), currently i={i}...")
        await asyncio.sleep(1)
        f *= i
    print(f"Task {name}: factorial({number}) = {f}")
    return f

async def main():
    # Schedule three calls *concurrently*:
    L = await asyncio.gather(
        factorial("A", 2),
        factorial("B", 3),
        factorial("C", 4),
    )
    print(L)

import nest_asyncio
nest_asyncio.apply()
asyncio.run(main())

import asyncio
import nest_asyncio
nest_asyncio.apply()

async def func():
    await asyncio.sleep(1000)
    print("func")

asyncio.run(func())


# ===========================================================

lst = [{"id":1, "name": "a"},{"id":2, "name": "b"},{"id":3, "name": "c"}]

list(t["id"] for t in lst)

1024/1792 

3/4