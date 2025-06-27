#Step 1: Granite Model installation
import json
import random
import os
import requests
import Encryptor
import PyPDF2
import streamlit as st
from streamlit import session_state as ss
from st_files_connection import FilesConnection as ss
from langchain_ollama.llms import OllamaLLM
from langchain_community.llms import Replicate  
from ibm_granite_community.notebook_utils import get_env_var
from transformers import AutoTokenizer

st.set_page_config(page_title="Wayfarer", layout="centered")
st.title("Wayfarer")
model_path = "ibm-granite/granite-3.3-8b-instruct"
repAPI = st.secrets["REPLICATE_API_TOKEN"]
model = Replicate(
    model = model_path,
    replicate_api_token=repAPI,
    model_kwargs={
        "temperature":0.0, #greedy
    },
)

#Strings for prompt error suggestions and main menu which will be repeated
menu = "-Include 'encrypt' and one uploaded file in your msg for the encrypted file and a one time key \n -Include 'validate', an uploaded file and 'key:<the selected key>' in your message to determine if the files are accurate \n -Type 'menu' to see this menu again  \n -Type 'exit' to quit.\n"

instructiontext = ""
if "instructions.pdf":
    reader = PyPDF2.PdfReader("instructions.pdf")
    for page in reader.pages:
        instructiontext += page.extract_text() or ""
tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False)


#Finding a particular string
def findStr(inputstr: str, beg:str, end:str):
    inputstr_lower = inputstr.lower()
    i = inputstr_lower.find(beg)

    #Check to see if the beginning bound is accurate
    if i == -1:
        return "" 

    i += len(beg)
    j = inputstr_lower[i:].find(end)

    #Adjust the end bound to be correct
    if j == -1:
        j = len(inputstr) 
    else:
        j += i + len(end)

    return inputstr[i:j]


#Session state startup to store chat_history without keys in future
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "username" not in st.session_state:
    st.session_state.username = ""

#User login
if not st.session_state.username:
    st.session_state.username = st.text_input("Enter your username to begin:", key="login_input")
    st.rerun()

st.success(f"""Welcome to the Wayfarer {st.session_state.username}, A tool designed to keep files secure. To do this I developed a way to encrypt the hash of your documents with a special 
          encryption key created from 3D pathfinding encryption. 3D pathfinding encryption requires picking a set of coordinates in a 3D space and making a path
          message for the set of instructions in order to get to that point. This message is then added onto your document's hash.  You can use this to ensure that documents shared by
          collegues and friends are legitamate by sharing the path key and validating them through this tool. Remember, you can only upload one document at a time, this tool cant handle multiple documents at the same time""")
st.write(f"{menu}")

#File Uploader
uploaded_file = st.file_uploader("Upload PDF document", type=["pdf"])
file_path = None

if uploaded_file:
    #Save uploaded file
    os.makedirs("temp", exist_ok=True)
    file_path=os.path.join("temp", uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"Uploaded: {uploaded_file.name}")
st.divider()

#Chatter
user_input = st.chat_input("Type your message...")

#The actual chat logic
if(user_input):
    history = st.session_state.chat_history
    respnse = ""

    #Encryption Logic
    if("encrypt" in user_input.lower()):
        tempSeed = random.random()
        if(file_path != None):
            output_bytes, signature = Encryptor.sign_pdf_embed(file_path,tempSeed, f"{tempSeed}" + ".pdf")
            response = "PDF signed  with embedded signature. Copy this one-time signature for comfirmation: "
            st.write(f"AI: {response}" + "Copy this one-time signature for comfirmation: " + f"{signature} \n")
            response += "Hidden for privacy reasons"
            st.download_button(
                label="Download Signed PDF",
                data=output_bytes,
                file_name=f"signed_{uploaded_file.name}",
                mime="application/pdf"
            )
        else:
            response = model.invoke(user_input + "The user's response was incorrect" + instructiontext) 
            user_input += user_input
            st.write(f"AI: {response}\n")
    #Validation logic
    elif("validate" in user_input.lower() and "key:" in user_input.lower()):
        keyToCompare = findStr(user_input, "key:", " ")
        if(file_path != None):
            response= Encryptor.verify_pdf_embedded(file_path, keyToCompare)
            userKey = user_input.find("key:")
            if(userKey == -1):
                userKey = len(user_input)
            user_input =user_input[:userKey] + "Hidden key for privacy reasons"
            st.write(f"AI: {response}\n")
            #Empty response keys
            fileToValidate = ""
            keyToCompare = ""
        else:
            response = model.invoke(user_input + "The user's response was incorrect" + instructiontext) 
            user_input = "Wrong Call (Hidden for Privacy reasons)"
            st.write(f"AI: {response}\n")
    #Help queries for menu
    elif(user_input.lower() == "menu"):
        response = menu
        st.write(f"AI: {response}\n")
    #All other queries
    else: 
        # Optionally, keep chat history for context:
        prompt = "\n".join([f"User: {h['user']}\nAI: {h['ai']}" for h in history])
        prompt +=  "\nUser: " + user_input + "\nAI:"
        
        # Call model
        response = model.invoke(prompt + instructiontext)

        
        st.write(f"AI: {response}\n")

    st.session_state.chat_history.append({"user": user_input, "ai" : response})

with st.sidebar:
    st.subheader("Chat History")
    for msg in st.session_state.chat_history:
        st.markdown(f"** {st.session_state.username}:** {msg['user']}")
        st.markdown(f"** AI:** {msg['ai']}")