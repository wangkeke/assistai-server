from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser

llm = ChatOpenAI(temperature=0, 
                 openai_api_key="123456789", 
                 openai_api_base="https://assistai-server.onrender.com/openai_agent")
prompt = PromptTemplate.from_template("Tell me a joke about {topic}")

chain = prompt | llm

print( chain.invoke({"topic": "bears"}) )

chain = (
    PromptTemplate.from_template(
        """Given the user question below, classify it as either being about `LangChain`, `Anthropic`, or `Other`.
                                     
Do not respond with more than one word.

<question>
{question}
</question>

Classification:"""
    )
    | llm
    | StrOutputParser()
)

print(chain.invoke({"question": "how do I call Anthropic?"}))

# 
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnableMap, RunnablePassthrough
from langchain.schema import format_document
from operator import itemgetter
from langchain.prompts import ChatPromptTemplate


llm = ChatOpenAI(temperature=0, 
                 openai_api_key="123456789", 
                 openai_api_base="https://assistai-server.onrender.com/openai_agent")
planner = (
    ChatPromptTemplate.from_template("Generate an argument about: {input}")
    | llm
    | StrOutputParser()
    | {"base_response": RunnablePassthrough()}
)

arguments_for = (
    ChatPromptTemplate.from_template(
        "List the pros or positive aspects of {base_response}"
    )
    | llm
    | StrOutputParser()
)
arguments_against = (
    ChatPromptTemplate.from_template(
        "List the cons or negative aspects of {base_response}"
    )
    | llm
    | StrOutputParser()
)

final_responder = (
    ChatPromptTemplate.from_messages(
        [
            ("ai", "{original_response}"),
            ("human", "Pros:\n{results_1}\n\nCons:\n{results_2}"),
            ("system", "Generate a final response given the critique\n\nTranslate to Chinese"),
        ]
    )
    | llm
    | StrOutputParser()
)

chain = (
    planner
    | {
        "results_1": arguments_for,
        "results_2": arguments_against,
        "original_response": itemgetter("base_response"),
    }
    | final_responder
)

chain.invoke({"input": "敏捷开发"})

# 

from langchain.prompts import ChatPromptTemplate

template = """Based on the table schema below, write a SQL query that would answer the user's question:
{schema}

Question: {question}
SQL Query:"""
prompt = ChatPromptTemplate.from_template(template)

from langchain.utilities import SQLDatabase

db = SQLDatabase.from_uri("sqlite:///./Chinook.db")
def get_schema(_):
    return db.get_table_info()

def run_query(query):
    return db.run(query)

from langchain.chat_models import ChatOpenAI
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough

model = ChatOpenAI(openai_api_key="123456789", 
                 openai_api_base="https://assistai-server.onrender.com/openai_agent")

sql_response = (
    RunnablePassthrough.assign(schema=get_schema)
    | prompt
    | model.bind(stop=["\nSQLResult:"])
    | StrOutputParser()
)
sql_response.invoke({"question": "How many employees are there?"})

