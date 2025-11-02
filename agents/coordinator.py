from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver  
from agents.sales_agent import query_sales_data
from agents.customer_agent import query_customer_data
import streamlit as st


@st.cache_resource(show_spinner=False)
def get_coordinator_agent():
    """
    Create and cache a unified Databricks query agent that coordinates both
    sales and customer data tools.
    """
    system_prompt = """You are a Databricks Query Agent.
    You have access to two specialized tools:
    -Customer info query tool
    -Sales data query tool

    For each user query:
    - Identify if it's about customers or sales.
    - Use the right tool(s) in order.
    - Return a clear, markdown-friendly answer.
    """

    agent = create_agent(
        model="gpt-4.1",
        tools=[query_customer_data, query_sales_data],
        system_prompt=system_prompt,
        checkpointer=InMemorySaver()
    )

    return agent
