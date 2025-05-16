import streamlit as st
from chatbot import custom_sql_agent
from states.agent_state import AgentState
from langchain_core.messages import AIMessage, HumanMessage

st.set_page_config(layout='wide', page_title='AI Chatbot', page_icon='💐')

if 'message_history' not in st.session_state:
    st.session_state.message_history = [AIMessage(content="Hiya, Im the AI chatbot. How can I help?")]

left_col, main_col, right_col = st.columns([1, 2, 1])

# 1. Buttons for chat - Clear Button

with left_col:
    if st.button('Clear Chat'):
        st.session_state.message_history = []


# 2. Chat history and input
with main_col:
    user_input = st.chat_input("Type here...")

    if user_input:
        st.session_state.message_history.append(HumanMessage(content=user_input))
    # Summary of annotation details associated with the 'Finance' hierarchy and added in the current month
        final_response = ""
        for step in custom_sql_agent.stream(
            AgentState(user_query=  user_input),
            stream_mode="updates"
        ):  
            print(step)
            final_response = step

        st.session_state.message_history.append(final_response["respond"]["final_response"])
        if "pdf_bytes" in final_response["respond"] and final_response["respond"]["pdf_bytes"]:
            st.download_button(
                label="📄 Download PDF Report",
                data=final_response["respond"]["pdf_bytes"],
                file_name="query_report.pdf",
                mime="application/pdf"
            )

    for i in range(1, len(st.session_state.message_history) + 1):
        this_message = st.session_state.message_history[-i]
        if isinstance(this_message, AIMessage):
            message_box = st.chat_message('assistant')
        else:
            message_box = st.chat_message('user')
        message_box.markdown(this_message.content)