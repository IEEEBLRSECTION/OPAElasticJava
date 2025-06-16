import streamlit as st
from LLMSuiteHandler import send_post_request_to_llm  # Import your backend function

# Initialize session state for conversation history and settings
if "messages" not in st.session_state:
    st.session_state.messages = []

# Default system prompt
DEFAULT_SYSTEM_PROMPT = """You are a helpful AI assistant created by DeepSeek. 
Your responses should be informative, concise, and professional. 
If you don't know the answer, say you don't know rather than making something up."""

# Sidebar for settings
with st.sidebar:
    st.title("Settings")
    
    # System prompt customization
    system_prompt = st.text_area(
        "System Prompt", 
        value=DEFAULT_SYSTEM_PROMPT,
        help="This guides the assistant's behavior"
    )
    
    # Model parameters
    st.subheader("Model Parameters")
    temperature = st.slider("Temperature", 0.0, 1.0, 0.7, help="Controls randomness")
    max_tokens = st.number_input("Max Tokens", 50, 2000, 500, help="Maximum response length")
    
    # Conversation controls
    st.subheader("Conversation Controls")
    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

def generate_response(user_input):
    """Generate response from LLM using conversation context"""
    # Prepare the conversation history including system prompt
    messages_for_llm = [{"role": "system", "content": system_prompt}]
    
    # Add previous conversation history (if any)
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            messages_for_llm.append({"role": "user", "content": msg["content"]})
        else:
            messages_for_llm.append({"role": "assistant", "content": msg["content"]})
    
    # Add the new user message
    messages_for_llm.append({"role": "user", "content": user_input})
    
    # Prepare parameters for the LLM call
    params = {
        "messages": messages_for_llm,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    # Send to your LLM backend
    response = send_post_request_to_llm(params)
    
    return response

# Main chat interface
st.title("DeepSeek-like Chat Assistant")
st.caption("A conversational AI assistant that maintains context")

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What would you like to know?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        # Simulate streaming response (adjust based on your backend capabilities)
        response = generate_response(prompt)
        full_response = response
        
        response_placeholder.markdown(full_response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
