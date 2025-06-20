import streamlit as st
from streamlit_extras.stylable_container import stylable_container
import requests
from bs4 import BeautifulSoup
import json
import random

# Load predefined prompts and workflows
def load_resources():
    with open('prompts.json', 'r') as f:
        prompts = json.load(f)
    with open('workflows.json', 'r') as f:
        workflows = json.load(f)
    return prompts, workflows

# Initialize session state
if 'input_text' not in st.session_state:
    st.session_state.input_text = ""
if 'show_workflow' not in st.session_state:
    st.session_state.show_workflow = False
if 'current_workflow' not in st.session_state:
    st.session_state.current_workflow = None
if 'suggestions' not in st.session_state:
    st.session_state.suggestions = []
if 'sandbox_url' not in st.session_state:
    st.session_state.sandbox_url = None
if 'search_executed' not in st.session_state:
    st.session_state.search_executed = False
if 'last_input' not in st.session_state:
    st.session_state.last_input = ""
if 'search_history' not in st.session_state:
    st.session_state.search_history = []

# Load resources
try:
    PROMPTS, WORKFLOWS = load_resources()
except:
    # Fallback data if files don't exist
    PROMPTS = {
        "general": [
            "What is the weather today?",
            "How to make a cake?",
            "Latest tech news",
            "Best restaurants nearby"
        ],
        "tech": [
            "How to use Python with Streamlit?",
            "What is AI?",
            "Latest JavaScript frameworks",
            "Cloud computing trends 2023"
        ]
    }
    
    WORKFLOWS = {
        "Search DeepSeek on Google": {
            "description": "Searches DeepSeek on Google and opens the first result",
            "steps": [
                {"action": "search_google", "query": "DeepSeek"},
                {"action": "open_first_result"}
            ]
        },
        "Find Python Documentation": {
            "description": "Finds and opens Python official documentation",
            "steps": [
                {"action": "search_google", "query": "Python official documentation"},
                {"action": "open_first_result"}
            ]
        }
    }

# Function to get Google search results
def search_google(query):
    try:
        url = f"https://www.google.com/search?q={query}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        for g in soup.find_all('div', class_='g'):
            anchor = g.find('a')
            if anchor and 'href' in anchor.attrs:
                link = anchor['href']
                title = g.find('h3')
                if title:
                    title = title.text
                    results.append({'title': title, 'link': link})
        
        return results[:3]  # Return top 3 results
    except Exception as e:
        st.error(f"Error performing search: {e}")
        return []

# Function to update suggestions
def update_suggestions():
    current_input = st.session_state.search_input
    if current_input != st.session_state.last_input:
        st.session_state.last_input = current_input
        if current_input:
            st.session_state.suggestions = get_suggested_prompts(current_input)
        else:
            st.session_state.suggestions = []
        st.session_state.search_executed = False

# Function to get suggested prompts
def get_suggested_prompts(input_text):
    input_text = input_text.strip().lower()
    if not input_text:
        return []
    suggestions = []
    # Search in general prompts
    for prompt in PROMPTS.get('general', []):
        if input_text in prompt.lower():
            suggestions.append(prompt)
    # If nothing found, search in tech prompts
    if not suggestions:
        for prompt in PROMPTS.get('tech', []):
            if input_text in prompt.lower():
                suggestions.append(prompt)
    # If still nothing, show random prompts
    if not suggestions:
        all_prompts = PROMPTS.get('general', []) + PROMPTS.get('tech', [])
        if all_prompts:
            suggestions = random.sample(all_prompts, min(3, len(all_prompts)))
    return suggestions[:5]  # Limit to top 5 suggestions

# Function to execute workflows
def execute_workflow(workflow_name):
    workflow = WORKFLOWS.get(workflow_name)
    if not workflow:
        st.error("Workflow not found")
        return
    
    st.session_state.show_workflow = True
    st.session_state.current_workflow = workflow_name
    st.session_state.sandbox_url = None
    st.session_state.search_executed = True
    
    st.write(f"## Executing Workflow: {workflow_name}")
    st.write(workflow['description'])
    
    for step in workflow['steps']:
        if step['action'] == "search_google":
            st.write(f"🔍 Searching Google for: {step['query']}")
            results = search_google(step['query'])
            st.session_state.search_results = results
            
            for i, result in enumerate(results, 1):
                st.write(f"{i}. {result['title']}")
                st.write(f"   {result['link']}")
                
        elif step['action'] == "open_first_result" and 'search_results' in st.session_state:
            if st.session_state.search_results:
                first_result = st.session_state.search_results[0]['link']
                st.write(f"🌐 First result: {first_result}")
                # Show a button to open in new tab
                st.markdown(
                    f'<a href="{first_result}" target="_blank"><button>Open First Result in New Tab</button></a>',
                    unsafe_allow_html=True
                )

# Main app
def main():
    st.set_page_config(page_title="Smart Search Engine", page_icon="🔍", layout="wide")
    
    # Custom CSS for Perplexity-like UI
    st.markdown("""
    <style>
    /* Main container styling */
    .stApp {
        background-color: #f9fafb;
    }
    
    /* Search bar styling */
    .stTextInput>div>div>input {
        padding: 16px 24px !important;
        border-radius: 24px !important;
        border: 1px solid #e5e7eb !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
        font-size: 16px !important;
    }
    
    /* Button styling */
    .stButton>button {
        border-radius: 24px !important;
        padding: 8px 24px !important;
        background-color: #3b82f6 !important;
        color: white !important;
        font-weight: 500 !important;
        border: none !important;
    }
    
    /* Suggestion cards */
    .prompt-suggestion {
        padding: 16px 20px;
        margin: 8px 0;
        border-radius: 12px;
        background-color: white;
        cursor: pointer;
        transition: all 0.2s;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .prompt-suggestion:hover {
        background-color: #f8fafc;
        border-color: #d1d5db;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Workflow cards */
    .workflow-card {
        padding: 16px 20px;
        margin: 12px 0;
        border-radius: 12px;
        background-color: white;
        border-left: 4px solid #3b82f6;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    /* Search result styling */
    .search-result {
        padding: 16px 20px;
        margin: 12px 0;
        border-radius: 12px;
        background-color: white;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #f9fafb !important;
        border-right: 1px solid #e5e7eb !important;
    }
    
    /* Sandbox container */
    .sandbox-container {
        width: 100%;
        height: 600px;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        margin-top: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    /* Title styling */
    h1 {
        color: #111827 !important;
    }
    
    /* Subtle text */
    .subtle-text {
        color: #6b7280;
        font-size: 0.9rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main header with logo
    col1, col2 = st.columns([0.1, 0.9])
    with col1:
        st.image("https://via.placeholder.com/40", width=40)  # Replace with your logo
    with col2:
        st.title("Smart Search")
    
    st.write("Ask anything and get instant answers with AI-powered search")
    
    # Before your text_input, add this logic:
    if 'selected_suggestion' in st.session_state:
        st.session_state.input_text = st.session_state.selected_suggestion
        st.session_state.search_input = st.session_state.selected_suggestion
        del st.session_state.selected_suggestion
    
    # Search input outside form for real-time suggestions
    def on_input_change():
        update_suggestions()

    # Main search bar with focus
    with st.container():
        user_input = st.text_input(
            "Ask anything...",
            value=st.session_state.input_text,
            key="search_input",
            placeholder="Ask anything or type '/' for commands",
            on_change=on_input_change,
            label_visibility="collapsed"
        )
    
    # Search button row
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        if st.button("Search", type="primary", use_container_width=True):
            st.session_state.input_text = user_input
            st.session_state.search_executed = True
            st.session_state.show_workflow = False
            st.session_state.sandbox_url = None
            if user_input:
                st.session_state.search_history.append(user_input)
            st.rerun()
    with col2:
        if st.button("I'm Feeling Lucky", use_container_width=True):
            st.session_state.input_text = random.choice(PROMPTS['general'] + PROMPTS['tech'])
            st.session_state.search_input = st.session_state.input_text
            st.session_state.search_executed = True
            st.rerun()
    
    # Update suggestions based on input changes
    if user_input != st.session_state.last_input:
        update_suggestions()
    
    # Show prompt suggestions while typing
    if st.session_state.suggestions and not st.session_state.search_executed:
        st.subheader("Suggested prompts", divider="gray")
        for suggestion in st.session_state.suggestions:
            with stylable_container(
                key=f"suggestion_{suggestion}",
                css_styles="""
                .prompt-suggestion {
                    padding: 16px 20px;
                    margin: 8px 0;
                    border-radius: 12px;
                    background-color: white;
                    cursor: pointer;
                    transition: all 0.2s;
                    border: 1px solid #e5e7eb;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
                }
                .prompt-suggestion:hover {
                    background-color: #f8fafc;
                    border-color: #d1d5db;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }
                """
            ):
                if st.button(suggestion, key=f"suggest_{suggestion}"):
                    st.session_state.selected_suggestion = suggestion
                    st.rerun()
    
    # Recent searches
    if st.session_state.search_history and not st.session_state.search_executed:
        st.subheader("Recent searches", divider="gray")
        for search in reversed(st.session_state.search_history[-5:]):
            if st.button(search, key=f"recent_{search}"):
                st.session_state.selected_suggestion = search
                st.rerun()
    
    # Show workflows section in sidebar
    with st.sidebar:
        st.markdown("### ⚡ Quick Actions")
        for workflow_name in WORKFLOWS:
            with st.expander(f"🔹 {workflow_name}"):
                st.caption(WORKFLOWS[workflow_name]['description'])
                if st.button(f"Run {workflow_name}", key=f"run_{workflow_name}", use_container_width=True):
                    execute_workflow(workflow_name)
                    st.rerun()
        
        st.markdown("---")
        st.markdown("### 🔍 Search Tools")
        st.caption("Advanced search options")
        # Add more tools here if needed
    
    # Main content area - show search results or workflow
    if st.session_state.search_executed and st.session_state.input_text and not st.session_state.show_workflow:
        st.subheader(f"Results for: {st.session_state.input_text}", divider="gray")
        
        # Simulate search results with AI summary (placeholder)
        with st.spinner("Searching with AI..."):
            st.markdown("""
            <div class="search-result">
                <h4>AI Summary</h4>
                <p>Here's a quick summary of what we found about your query...</p>
            </div>
            """, unsafe_allow_html=True)
            
            results = search_google(st.session_state.input_text)
        
        if results:
            for i, result in enumerate(results, 1):
                with st.container():
                    st.markdown(f"""
                    <div class="search-result">
                        <h4>{result['title']}</h4>
                        <p class="subtle-text">{result['link']}</p>
                        <p>Sample content from the page would appear here in a real implementation...</p>
                        <div style="display: flex; gap: 8px; margin-top: 12px;">
                            <a href="{result['link']}" target="_blank"><button style="padding: 6px 12px; border-radius: 6px; background: #3b82f6; color: white; border: none; font-size: 14px;">Visit</button></a>
                            <button style="padding: 6px 12px; border-radius: 6px; background: #f9fafb; color: #111827; border: 1px solid #e5e7eb; font-size: 14px;">Share</button>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("No results found. Try a different query.")
    
    elif st.session_state.show_workflow:
        execute_workflow(st.session_state.current_workflow)
    
    # Sandbox area for displaying pages
    if st.session_state.sandbox_url:
        st.markdown(f"""
        <div class="sandbox-container">
            <iframe src="{st.session_state.sandbox_url}" width="100%" height="100%" style="border:none;"></iframe>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
