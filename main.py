import os
import time
import io
from pathlib import Path
filepath=os.path.realpath(__file__)
filepath=Path(filepath)
import streamlit as st
from langsmith import Client
from src.appointment_scheduling.schedule_appointment import agent
from audio_recorder_streamlit import audio_recorder
from langchain_core.tracers.context import collect_runs
from langchain.schema.runnable import RunnableConfig
from langchain.memory import ConversationBufferMemory
from streamlit_feedback import streamlit_feedback
from langchain_community.callbacks.streamlit import (
    StreamlitCallbackHandler,
)

client = Client()
score_mappings = {
        "thumbs": {"👍": 1, "👎": 0},
        "faces": {"😀": 1, "🙂": 0.75, "😐": 0.5, "🙁": 0.25, "😞": 0},
    }

if "run_id" not in st.session_state:
    st.session_state.run_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
def _reset_feedback():
    st.session_state.feedback_update = None
    st.session_state.feedback = None
    
# React to user input
if prompt := st.chat_input("Please ask your query"):
    st.chat_message("user").markdown(prompt)
    _reset_feedback()
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    if st.session_state.messages[-1]["role"] != 'assistant':
        with st.chat_message("assistant"):
            with collect_runs() as runs_cb:
                st_callback = StreamlitCallbackHandler(st.container())
                bot_response = agent(prompt,st_callback)
                st.write(bot_response)
                st.session_state.messages.append({"role":"assistant","content":bot_response})
                st.session_state.run_id = runs_cb.traced_runs[0].id
            
if st.session_state.get("run_id"):
    run_id = st.session_state.run_id
    feedback = streamlit_feedback(
        feedback_type="thumbs",
        optional_text_label="[Optional] Please provide an explanation",
        key=f"feedback_{run_id}",
    )
    scores = score_mappings["thumbs"]
    if feedback:
            score = scores.get(feedback["score"])
            if score is not None:
                feedback_type_str = f"thumbs {feedback['score']}"
                feedback_record = client.create_feedback(
                    run_id,
                    feedback_type_str,
                    score=score,
                    comment=feedback.get("text"),
                )
                st.session_state.feedback = {
                    "feedback_id": str(feedback_record.id),
                    "score": score,
                }
            else:
                st.warning("Invalid feedback score.")
        
