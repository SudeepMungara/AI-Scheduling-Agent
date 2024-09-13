import os
import time
import pickle
import yaml
import pandas as pd
from src.utils import read_yaml
from pathlib import Path
filepath=os.path.realpath(__file__)
filepath=Path(filepath)
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain.agents import AgentExecutor,create_tool_calling_agent,create_structured_chat_agent
from langchain.schema.runnable import RunnablePassthrough
from langchain.tools.render import render_text_description
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ChatMessageHistory,ConversationBufferMemory,StreamlitChatMessageHistory
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from src.appointment_scheduling.prompt import SYSTEM_PROMPT
from src.appointment_scheduling.evaluator import evaluate_agent
from src.appointment_scheduling.tools import get_available_specialites, get_doctor_timeslot, get_available_dates, get_coverage_info
from src.appointment_scheduling.tools import get_doctor_using_speciality, book_appointment, verify_existing_patient, add_new_patient, reschedule_patient_appointment
from src.appointment_scheduling.tools import get_patient_appointment_details, cancel_doctor_appointment,get_current_date,update_coverage_info
load_dotenv()

params = read_yaml()

tools= [get_available_specialites,
        get_doctor_timeslot,
        get_available_dates,
        get_coverage_info,
        update_coverage_info,
        get_doctor_using_speciality,
        book_appointment,
        verify_existing_patient,
        add_new_patient,
        reschedule_patient_appointment,
        get_patient_appointment_details,
        cancel_doctor_appointment,
        get_current_date]

functions = [convert_to_openai_function(f) for f in tools]

model = AzureChatOpenAI(
    openai_api_version=params["OPENAI_API_VERSION"],
    azure_deployment=params["AZURE_DEPLOYMENT"],
    temperature = params["TEMPERATURE"]
    
).bind(functions=functions)

tool_definitions = render_text_description(tools)
            
prompt = ChatPromptTemplate.from_messages([("system", SYSTEM_PROMPT),
                                            MessagesPlaceholder(variable_name="tool_definitions"),
                                            MessagesPlaceholder(variable_name="chat_history"), 
                                            ("user", "{input}"),
                                            MessagesPlaceholder(variable_name="agent_scratchpad")])
message_history = ChatMessageHistory()

memory = ConversationBufferMemory(
    memory_key="chat_history",
    input_key = "input",
    chat_memory=message_history,
    output_key="output",
    return_messages=True
)

def agent(input:str,callback):
    
    chain = RunnablePassthrough.assign(agent_scratchpad=lambda x: format_to_openai_functions(x["intermediate_steps"]))| prompt | model | OpenAIFunctionsAgentOutputParser()
    # chain = create_tool_calling_agent(model,tools,prompt)
    agent_executor = AgentExecutor(agent=chain, tools=tools, memory=memory, verbose=True,return_intermediate_steps=True)
    output = agent_executor.invoke({"input":input,"tool_definitions":[tool_definitions]},{"callbacks": [callback]})
    print(evaluate_agent(output))
    return output['output']
    

