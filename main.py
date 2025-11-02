import streamlit as st
import asyncio
import os
import uuid
from agents.coordinator import get_coordinator_agent
from dotenv import load_dotenv

load_dotenv()

# ========================
# 🧠 STREAMLIT CONFIG
# ========================
st.set_page_config(page_title="Databricks Query Agent", layout="wide")
st.title("Databricks Genie Query Agent")

# Initialize session state
if "threads" not in st.session_state:
    st.session_state.threads = {}  # {uuid: {"messages": [...], "title": str}}
if "active_thread" not in st.session_state:
    st.session_state.active_thread = None

# ========================
# ➕ CREATE NEW CHAT BUTTON
# ========================
col1, col2 = st.columns([0.15, 0.85])
with col1:
    if st.button("New Chat", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.threads[new_id] = {"messages": [], "title": "New chat"}
        st.session_state.active_thread = new_id
        st.rerun()
with col2:
    st.markdown("##### Active Conversation")

# ========================
# 🧾 THREAD SIDEBAR (on right)
# ========================
with st.sidebar:
    st.header("Chats 🔗")
    if st.session_state.threads:
        for thread_id, thread_data in st.session_state.threads.items():
            btn_label = thread_data.get("title", "Unnamed chat")
            if st.button(btn_label, key=thread_id):
                st.session_state.active_thread = thread_id
                st.rerun()
    else:
        st.info("No chats yet. Start a new one!")

# ========================
# 🧵 LOAD ACTIVE THREAD
# ========================
if st.session_state.active_thread is None:
    st.warning("👆 Click 'New Chat' to start a conversation")
    st.stop()

thread_id = st.session_state.active_thread
thread_data = st.session_state.threads[thread_id]
messages = thread_data["messages"]

# Render past messages
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Ask about sales or customer data...")

# ========================
# 🌀 STREAM RESPONSE FUNCTION
# ========================
async def stream_response(query: str):
    agent = get_coordinator_agent()
    input_message = {"messages": [{"role": "user", "content": query}]}
    final_output = ""
    tool_updates = []
    response_box = st.empty()
    sidebar_box = st.sidebar.empty()
    config = {"configurable": {"thread_id": thread_id}}

    async for event in agent.astream_events(input_message, config, version="v1"):
        kind = event["event"]
        if kind == "on_chat_model_stream":
            token = event["data"]["chunk"].content
            final_output += token
            response_box.markdown(final_output)
        elif kind == "on_tool_start":
            tool_name = event["name"]
            args = event["data"]["input"]
            tool_updates.append(f"🧰 **{tool_name}** called with args: {args}")
            sidebar_box.markdown("\n\n".join(tool_updates))
        elif kind == "on_tool_end":
            tool_updates.append("✅ Tool finished execution\n")
            sidebar_box.markdown("\n\n".join(tool_updates))

    return final_output

# ========================
# 🚀 ON MESSAGE SUBMIT
# ========================
if user_input:
    # Store user message
    messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    with st.chat_message("assistant"):
        response = asyncio.run(stream_response(user_input))
        messages.append({"role": "assistant", "content": response})

    # Update thread title if it's the first message
    if thread_data["title"] == "New chat":
        thread_data["title"] = user_input[:30] + ("..." if len(user_input) > 30 else "")
    st.session_state.threads[thread_id] = thread_data
    st.rerun()