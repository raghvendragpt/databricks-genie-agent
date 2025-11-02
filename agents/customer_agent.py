from databricks_ai_bridge.genie import Genie
from langchain.tools import tool
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()


@lru_cache(maxsize=1)
def get_customer_client():
    """Cache and reuse Databricks Genie customer client."""
    return Genie(space_id=os.getenv("CUSTOMER_SPACE_ID"))


@tool
def query_customer_data(detailed_question: str):
    """
    Query AWS Databricks Genie customer data (columns: customer_id, segment, lifetime_value, churn_risk, region)
    and return the data in markdown format.
    """
    client = get_customer_client()
    data = client.ask_question(detailed_question)
    return data.result
