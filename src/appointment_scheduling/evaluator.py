from typing import Any, Optional, Sequence, Tuple
from langchain.evaluation import load_evaluator,AgentTrajectoryEvaluator
from langchain_core.agents import AgentAction
from langchain_openai import AzureChatOpenAI
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain.tools.render import render_text_description
from src.appointment_scheduling.prompt import SYSTEM_PROMPT,EVALUATION_PROMPT,SCHEDULE_PROMPT,RESCHEDULE_PROMPT,CANCEL_PROMPT, EVALUATION_PROMPT
from src.appointment_scheduling.tools import get_available_specialites, get_doctor_timeslot, get_available_dates, get_coverage_info
from src.appointment_scheduling.tools import get_doctor_using_speciality, book_appointment, verify_existing_patient, add_new_patient, reschedule_patient_appointment
from src.appointment_scheduling.tools import get_patient_appointment_details, cancel_doctor_appointment,get_current_date,update_coverage_info
from src.utils import read_yaml


class ToolUsageEvaluator(AgentTrajectoryEvaluator):

    def __init__(self)-> None:
        params = read_yaml()
        
        llm = AzureChatOpenAI(
                openai_api_version=params["OPENAI_API_VERSION"],
                azure_deployment=params["AZURE_DEPLOYMENT"],
                temperature = params["TEMPERATURE"])
        
        tools =[get_available_specialites,
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
        
        self.schedule_prompt = SCHEDULE_PROMPT,
        self.reschedule_prompt = RESCHEDULE_PROMPT,
        self.cancel_prompt =  CANCEL_PROMPT,
        self.tool_definitions = tool_definitions = render_text_description(tools)
        template = PromptTemplate.from_template(EVALUATION_PROMPT)
        parser = JsonOutputParser()
        self.chain = template | llm | parser
    
    def _evaluate_agent_trajectory(
        self,
        *,
        chat_history: list,
        prediction: str,
        input: str,
        agent_trajectory: Sequence[Tuple[AgentAction, str]],
        reference: Optional[str] = None,
        **kwargs: Any,
    ) -> dict:
        vals = [
            f"{i}: Action=[{action.tool}] returned observation = [{observation}]"
            for i, (action, observation) in enumerate(agent_trajectory)
        ]
        trajectory = "\n".join(vals)
        response = self.chain.invoke(dict(
            schedule_prompt = self.schedule_prompt,
            reschedule_prompt = self.reschedule_prompt,
            cancel_prompt =  self.cancel_prompt,
            tool_definitions = self.tool_definitions,
            chat_history = chat_history,
            trajectory=trajectory, 
            question=input,
            output = prediction), **kwargs)
        return response



def evaluate_agent(result:dict):
    params = read_yaml()
    llm = AzureChatOpenAI(
    openai_api_version=params["OPENAI_API_VERSION"],
    azure_deployment=params["AZURE_DEPLOYMENT"],
    temperature = params["TEMPERATURE"]
    )
    evaluator = ToolUsageEvaluator()

    evaluation_result = evaluator.evaluate_agent_trajectory(
        prediction=result["output"],
        input=result["input"],
        agent_trajectory=result["intermediate_steps"],
        chat_history = result['chat_history']) 
    return evaluation_result
