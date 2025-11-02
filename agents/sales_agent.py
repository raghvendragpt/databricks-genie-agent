from databricks_ai_bridge.genie import Genie
from langchain.tools import tool
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()



@lru_cache(maxsize=1)
def get_sales_client():
    """Cache and reuse Databricks Genie sales client."""
    return Genie(space_id=os.getenv("SALES_SPACE_ID"))


@tool
def query_sales_data(detailed_question: str):
    """
    Query AWS Databricks Genie sales data (columns: date, product, category, revenue, region)
    and return the data in markdown format.
    """
    client = get_sales_client()
    data = client.ask_question(detailed_question)
    return data.result
