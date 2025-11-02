# Agent Chatbot (Databricks Query Agent)

This folder contains a Streamlit-based conversational front-end that coordinates specialized agents to query Databricks (via a Genie bridge). The app routes user chat queries to the appropriate tool (sales or customer data) and streams responses back to the UI.

## What is included
- `main.py` — Streamlit app and UI (chat threads, streaming responses).
- `agents/` — package containing agent tools and the coordinator:
  - `coordinator.py` — creates and caches a coordinator agent that knows two tools.
  - `customer_agent.py` — Databricks Genie client + tool for customer queries.
  - `sales_agent.py` — Databricks Genie client + tool for sales queries.

## Quick contract (inputs / outputs)
- Input: user text queries entered in the Streamlit chat UI.
- Output: assistant responses rendered in the Streamlit chat area (markdown), plus sidebar tool call updates.

## Prerequisites
- Python 3.11+ (3.12+ recommended)
- Windows (instructions below use cmd.exe)

Create environment and install the dependencies:

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Required environment variables (.env sample)
Create a `.env` file or set these variables in your environment. Below are all variables the code references directly plus common provider vars you will likely need.

Space variables for respective tools and Genie space:

```
CUSTOMER_SPACE_ID=your-customer-space-id
SALES_SPACE_ID=your-sales-space-id
```

Databricks and Openai connection variables:

```
# Example for OpenAI
OPENAI_API_KEY=sk-...

# Example for Databricks (if you use Databricks REST/token auth)
DATABRICKS_HOST=https://<your-databricks-instance>
DATABRICKS_TOKEN=dapi...
```

## How to run (developer / local)
From a Windows cmd shell, run:

```
streamlit run main.py
```

This will open a Streamlit UI in your browser. Use the "New Chat" button to start a conversation and ask about sales or customer data.

## Architecture diagram (ASCII)

The diagram below shows the main components and the data flow.

```
+-----------------------------+
|  Streamlit UI (main.py)    |
|  - Chat threads & session   |
|  - stream_response()        |
+-----------------------------+
              |
              | gets/streams responses
              v
+-----------------------------+
|  Coordinator agent          |
|  (agents/coordinator.py)    |
|  - create_agent(...)        |
|  - tools: [query_customer,  |
|           query_sales]      |
+-----------------------------+
         /                  \
        /                    \
       v                      v
+----------------+      +----------------+
| customer_agent |      | sales_agent    |
| (customer_tool)|      | (sales_tool)   |
| - get_customer_client()| - get_sales_client()|
| - uses Genie(space_id) | - uses Genie(space_id)|
+----------------+      +----------------+
       |                      |
       | calls Databricks      | calls Databricks
       v                      v
   Databricks Genie API (query execution and results)
```

Notes:
- `main.py` obtains a cached coordinator from `agents.coordinator.get_coordinator_agent()` and streams agent events back to the UI.
- The coordinator uses `langchain` agent patterns and the two tool functions to dispatch queries to the correct Databricks Genie bridge.


## Sample questions and answers

Q: What regions have high churn rate but also high revenue?

A: Based on the available data:

- The South region has a high customer churn risk.
- Both the North and South regions have high revenue, with North generating the highest revenue, followed by South.

Therefore, the South region is notable for having both a high churn risk and high revenue. You may want to focus retention efforts in this region to protect significant revenue.

---

Q: Compare sales performance with customer segments

A: Here is a comparison of sales performance with customer segments by region:

| Region | Total Revenue | Dominant Customer Segment | Customer Count |
|--------|---------------:|--------------------------|---------------:|
| North  | 2,525          | Premium                  | 2              |
| South  | 750            | Standard                 | 1              |

Insights:

- The North region, with the Premium segment, generates significantly higher revenue.
- The South region, dominated by the Standard segment, has lower revenue.
This suggests a strong association between the presence of Premium customers and higher sales performance in the North region.
---

## Conversation threads and history

The app maintains chat threads and conversation history using three cooperating mechanisms:

- Streamlit session state: `st.session_state` holds the active chat threads and UI state for the current browser session. Each thread object contains metadata (title, created_at, last_updated) and a `thread_id` used to look up saved history.

- LangChain InMemorySaver(): when the app runs a conversation or receives an agent response, the text and metadata are saved to an in-memory conversation store via LangChain's `InMemorySaver()` (or a small wrapper around it). This keeps recent messages available for quick access and for building context when sending follow-up queries.

- thread_ids mapping: each chat thread has a unique `thread_id` that is used as the key to link the Streamlit session entry and the LangChain saver records. This lets the app reconstruct a thread's conversation by loading messages from the saver using the `thread_id` and rendering them from `st.session_state`.

Together these parts provide a lightweight, fast in-session history mechanism:

- UI layer: `st.session_state['threads']` (or similar) drives what the user sees and which thread is active.
- Persistence layer (in-memory): `InMemorySaver()` stores the ordered messages for a given `thread_id` so the coordinator and agents can build context for LLM calls.
- Routing: the `thread_id` ties the two layers together and is carried with each tool call / agent invocation so history can be retrieved and appended.

Implementation notes / common pitfalls
- If you need longer-lived persistence across server restarts, replace `InMemorySaver()` with a durable saver (e.g., an on-disk or database-backed LangChain state saver) and ensure `thread_id` is stable and serializable.
- Carefully guard large histories: truncate or summarize long threads before sending them as context to an LLM to avoid token limits and high costs.
- If multiple browser sessions must share the same thread, persist thread metadata externally and sync `st.session_state` on load using the shared `thread_id` as the canonical key.

Example (pseudo):

- On new thread creation:
  - generate `thread_id`
  - append thread metadata into `st.session_state['threads']`
  - create an empty InMemorySaver entry for `thread_id`

- On user message or agent response:
  - save the message to `InMemorySaver()` with the `thread_id`
  - update `st.session_state['threads'][active]['last_updated']`
  - re-render the chat UI from `InMemorySaver()` (or session_state cache)

This approach keeps the UI responsive while providing an explicit mapping between UI threads and the conversation history used to supply context to the coordinator and agents.