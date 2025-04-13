import streamlit as st
import json
import requests
import os
from dotenv import load_dotenv
from openai import OpenAI

# 🌍 Load API keys from .env file
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 🎯 Tool 1: Get Weather
def get_weather(city: str):
    url = f"https://wttr.in/{city}?format=%C+%t"
    response = requests.get(url)
    if response.status_code == 200:
        return f"🌦️ The weather in **{city}** is `{response.text.strip()}`."
    return "❌ Unable to fetch weather at the moment."

# 🎯 Tool 2: Google Search
def google_search(query: str):
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={api_key}&cx={cse_id}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        results = []
        for item in data.get("items", [])[:3]:
            results.append(f"🔹 **{item['title']}**\n🔗 {item['link']}")
        return "\n\n".join(results) or "No results found."
    return f"❌ Search failed: {response.status_code} - {response.text}"

# 🧰 Tool registry
available_tools = {
    "get_weather": {
        "fn": get_weather,
        "description": "Takes a city name and returns current weather."
    },
    "google_search": {
        "fn": google_search,
        "description": "Takes a query and returns top 3 Google search results."
    },
}

# 🧠 LLM System Prompt
system_prompt = f'''
You are a helpful AI assistant. Think step-by-step.
You can use tools: weather and Google search when needed.
Respond with JSON structure like:
{{
  "step": "plan" | "action" | "observe" | "output",
  "content": "text",
  "function": "tool_name_if_needed",
  "input": "input_for_tool"
}}
Tools:
{json.dumps({k: v['description'] for k, v in available_tools.items()}, indent=4)}
'''

# 🌐 Streamlit App Configuration
st.set_page_config(page_title="Smart Assistant 🤖", layout="centered", page_icon="🧠")

# 🎨 Stylish CSS
st.markdown("""
    <style>
        body {
            background-color: #F5F7FA;
        }
        .main {
            background: white;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);
        }
        .stTextInput > div > div > input {
            padding: 12px;
            border-radius: 10px;
            border: 1px solid #6A5ACD;
            font-size: 1.1em;
        }
        .stButton > button {
            background-color: #6A5ACD;
            color: white;
            font-weight: bold;
            padding: 10px 16px;
            border-radius: 10px;
            font-size: 1.1em;
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            background-color: #836FFF;
        }
    </style>
""", unsafe_allow_html=True)

# 🧠 Title & Intro
st.markdown("<h1 style='text-align:center; color:#6A5ACD;'>🧠 Smart Assistant Bot</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; font-size:1.1em;'>Ask anything — Weather, Search, & More.</p>", unsafe_allow_html=True)

# 🗨️ Chat History
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": system_prompt}]

# 🔍 User Input
col1, col2 = st.columns([5, 1])
with col1:
    user_query = st.text_input("Type your query", placeholder="E.g. What’s the weather in Lahore?")
with col2:
    ask_btn = st.button("Ask 💬", use_container_width=True)

# 💬 Chat loop logic
def process_chat():
    with st.spinner("🤔 Thinking..."):
        while True:
            response = client.chat.completions.create(
                model="gpt-4o",
                temperature=0.5,
                messages=st.session_state.messages
            )
            reply = response.choices[0].message.content

            try:
                parsed = json.loads(reply)
            except json.JSONDecodeError:
                st.error("⚠️ LLM response was not in expected JSON format.")
                st.session_state.messages.append({"role": "assistant", "content": reply})
                break

            st.session_state.messages.append({"role": "assistant", "content": json.dumps(parsed)})
            step = parsed.get("step")

            if step == "plan":
                st.info(f"📌 **Plan**: {parsed['content']}")
                continue

            elif step == "action":
                tool_name = parsed.get("function")
                tool_input = parsed.get("input")
                if tool_name in available_tools:
                    tool_output = available_tools[tool_name]["fn"](tool_input)
                    st.session_state.messages.append({"role": "assistant", "content": json.dumps({
                        "step": "observe",
                        "content": tool_output
                    })})
                    st.success(f"📡 **Observation**: {tool_output}")
                    continue

            elif step == "output":
                st.markdown(f"""
                    <div style='background-color:#F0F8FF;padding:15px;border-radius:10px;border-left:5px solid #6A5ACD;'>
                        <strong>🤖 Final Answer:</strong><br>{parsed['content']}
                    </div>
                """, unsafe_allow_html=True)
                break
            else:
                st.warning("⚠️ Unrecognized step.")
                break

# 🚀 Trigger processing
if ask_btn and user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    process_chat()
