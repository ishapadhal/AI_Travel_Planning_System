'''
# pip install langgraph langchain langchain-openai langchain-groq langchain-community langchain-tavily psycopg[binary] psycopg_pool python-dotenv tavily-python pip install requests streamlit

# install PostgresSql and create database
CREATE DATABASE langgraph_memory;  ( or open pgadmin4 and create database there )
'''
# LangGraph Multi-Agent Travel Booking System with Long-Term Memory

# main.py
import os
import streamlit as st
from typing import TypedDict, Annotated
import operator

import psycopg
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)

from langchain_groq import ChatGroq

from tools.tavily_tool import tavily_search
from tools.flight_tool import search_flights
from dotenv import load_dotenv
load_dotenv()

print("STEP 1: Starting main.py")

print("STEP 2: Getting DATABASE_URL")

DATABASE_URL = st.secrets["DATABASE_URL"]

print("STEP 3: DATABASE_URL loaded")

_conn = psycopg.connect(DATABASE_URL, autocommit=True)

print("STEP 4: PostgreSQL connected")

checkpointer = PostgresSaver(_conn)

print("STEP 5: PostgresSaver created")

checkpointer.setup()

print("STEP 6: Checkpointer setup complete")

print("STEP 7: Creating graph")
print("STEP 8: Graph created")
print("STEP 9: Creating LLM")
print("STEP 10: LLM created")
print("STEP 11: After LLM setup")
print("STEP 12: Before app UI")
print("STEP 13: App UI started")


# LLM
llm = ChatGroq(
    model="openai/gpt-oss-120b"
)

# State
class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str
    flight_results: str
    hotel_results: str
    itinerary: str
    llm_calls: int

# Flight Agent
def flight_agent(state: TravelState):
    query = state["user_query"]
    flight_data = search_flights(query)
    return {
        "flight_results": flight_data,
        "messages": [
            AIMessage(content=f"Flight results fetched")
        ],
        "llm_calls": state.get("llm_calls", 0) + 1
    }

# Hotel Agent
def hotel_agent(state: TravelState):
    query = f"Best hotels for {state['user_query']}"
    hotel_results = tavily_search(query)

    return {
        "hotel_results": hotel_results,
        "messages": [
            AIMessage(content="Hotel information fetched")
        ],
        "llm_calls": state.get("llm_calls", 0) + 1
    }

# Itinerary Agent
def itinerary_agent(state: TravelState):

    prompt = f"""
    Create a travel itinerary.
    User Query:
    {state['user_query']}

    Flight Results:
    {state['flight_results']}

    Hotel Results:
    {state['hotel_results']}
    """

    response = llm.invoke([
        SystemMessage(
            content="You are an expert travel planner"
        ),
        HumanMessage(content=prompt)
    ])

    return {
        "itinerary": response.content,
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }

# Final Response Agent
def final_agent(state: TravelState):

    final_prompt = f"""
    Generate final travel response.

    Flights:
    {state['flight_results']}

    Hotels:
    {state['hotel_results']}

    Itinerary:
    {state['itinerary']}
    """

    response = llm.invoke([
        HumanMessage(content=final_prompt)
    ])

    return {
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


graph = StateGraph(TravelState)

graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_agent", hotel_agent)
graph.add_node("itinerary_agent", itinerary_agent)
graph.add_node("final_agent", final_agent)

graph.add_edge(START, "flight_agent")
graph.add_edge("flight_agent", "hotel_agent")
graph.add_edge("hotel_agent", "itinerary_agent")
graph.add_edge("itinerary_agent", "final_agent")
graph.add_edge("final_agent", END)


# Persistent connection so both CLI and Streamlit can share the compiled app

app = graph.compile(checkpointer=checkpointer)

# =========================
# STREAMLIT UI
# =========================

st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="✈️",
    layout="wide"
)

st.markdown("""
<style>

/* ---------- GLOBAL ---------- */
.stApp {
    background: linear-gradient(135deg, #f7f9fc 0%, #eef4ff 100%);
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1200px;
}

/* ---------- HERO ---------- */
.hero {
    padding: 45px 40px;
    border-radius: 25px;
    background: linear-gradient(135deg, #0f172a, #1e3a8a);
    color: white;
    text-align: center;
    margin-bottom: 30px;
    box-shadow: 0 15px 40px rgba(15, 23, 42, 0.20);
}

.hero h1 {
    font-size: 48px;
    margin-bottom: 10px;
    font-weight: 800;
}

.hero p {
    font-size: 19px;
    color: #dbeafe;
    margin-bottom: 0;
}

/* ---------- FEATURE CARDS ---------- */
.feature-card {
    background: white;
    padding: 22px;
    border-radius: 18px;
    text-align: center;
    height: 140px;
    box-shadow: 0 8px 25px rgba(15, 23, 42, 0.08);
    border: 1px solid #e5e7eb;
}

.feature-icon {
    font-size: 32px;
    margin-bottom: 8px;
}

.feature-title {
    font-size: 17px;
    font-weight: 700;
    color: #111827;
}

.feature-text {
    font-size: 13px;
    color: #6b7280;
}

/* ---------- INPUT AREA ---------- */
.input-card {
    background: white;
    padding: 30px;
    border-radius: 22px;
    margin-top: 30px;
    margin-bottom: 25px;
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
}

/* ---------- BUTTON ---------- */
.stButton > button {
    width: 100%;
    border-radius: 12px;
    height: 50px;
    font-size: 17px;
    font-weight: 700;
    border: none;
    background: linear-gradient(90deg, #2563eb, #4f46e5);
    color: white;
    transition: all 0.25s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(37, 99, 235, 0.30);
}

/* ---------- TEXT INPUT ---------- */
.stTextInput > div > div > input {
    border-radius: 12px;
    border: 2px solid #e5e7eb;
    padding: 14px;
    font-size: 16px;
}

.stTextInput > div > div > input:focus {
    border-color: #2563eb;
    box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15);
}

/* ---------- RESULT ---------- */
.result-box {
    background: white;
    padding: 30px;
    border-radius: 22px;
    margin-top: 25px;
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.10);
    border-left: 5px solid #2563eb;
}

.result-title {
    font-size: 25px;
    font-weight: 800;
    color: #111827;
    margin-bottom: 15px;
}

/* ---------- FOOTER ---------- */
.footer {
    text-align: center;
    color: #6b7280;
    font-size: 13px;
    margin-top: 50px;
    padding: 20px;
}

</style>
""", unsafe_allow_html=True)


# =========================
# HERO
# =========================

st.markdown("""
<div class="hero">

<h1>✈️ AI Travel Planner</h1>

<p>
Plan flights, discover hotels and generate personalized itineraries
with the power of AI.
</p>

</div>
""", unsafe_allow_html=True)


# =========================
# FEATURES
# =========================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">✈️</div>
        <div class="feature-title">Flight Search</div>
        <div class="feature-text">Find suitable flights</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🏨</div>
        <div class="feature-title">Hotels</div>
        <div class="feature-text">Discover places to stay</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🗺️</div>
        <div class="feature-title">Itinerary</div>
        <div class="feature-text">Build your trip plan</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🤖</div>
        <div class="feature-title">AI Planner</div>
        <div class="feature-text">Powered by LLMs</div>
    </div>
    """, unsafe_allow_html=True)


# =========================
# INPUT
# =========================

st.markdown("""
<div class="input-card">
<h3>🌎 Where do you want to go?</h3>
<p style="color:#6b7280;">
Tell our AI what kind of trip you are planning.
</p>
</div>
""", unsafe_allow_html=True)


user_input = st.text_input(
    "",
    placeholder="Example: Plan a 5-day trip from Mumbai to Dubai..."
)


if st.button("✨ Plan My Trip"):

    if user_input:

        config = {
            "configurable": {
                "thread_id": "streamlit_user"
            }
        }

        with st.spinner("🤖 AI is planning your perfect trip..."):

            result = app.invoke(
                {
                    "messages": [
                        HumanMessage(content=user_input)
                    ],
                    "user_query": user_input,
                    "flight_results": "",
                    "hotel_results": "",
                    "itinerary": "",
                    "llm_calls": 0
                },
                config=config
            )

        st.markdown("""
        <div class="result-box">
        <div class="result-title">🌍 Your Travel Plan</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(result["messages"][-1].content)

    else:

        st.warning("Please enter a travel request first.")


# =========================
# FOOTER
# =========================

st.markdown("""
<div class="footer">
✈️ AI Travel Planning System &nbsp; • &nbsp;
Powered by LangGraph + Groq + PostgreSQL
</div>
""", unsafe_allow_html=True)
