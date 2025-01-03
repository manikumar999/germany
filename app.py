import streamlit as st
import pandas as pd
import json
import os
from pdf2image import convert_from_bytes
from io import BytesIO
import base64
from openai import OpenAI

#SET OPEN AI KEY
# os.environ["OPENAI_API_KEY"] = os.environ["OPENAI_API_KEY_DEV"]

# set streamlit layout wide
st.set_page_config(layout="wide")
client = OpenAI()

poppler_path = r"poppler-24.08.0\Library\bin" 
# use os to get poppler_path
# poppler_path = os.path.join("poppler-24.08.0", "Library", "bin")
# print(poppler_path)
API_KEY = "manitcs123"

def authenticate_api_key(api_key):
    if api_key != API_KEY:
        return False
    return True

def process_images_extract_json(base64_images):
    response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": """
            You will be given one or more images containing details of one or more conferences or meetings, such as the name, time, location, and more. 
            Carefully analyze each image and extract the following specific fields for each conference or meeting:

                1. Name of the conference/meeting

                2. Time

                3. Location

                4. Date

                5. Key speakers and related topics

                6. Organizer's name

                7. Agenda of the conference/meeting
                
                8. Phone number

            Return the extracted information strictly in JSON format. The JSON should follow the structure below:
            {
            "ConferenceDetails": [
                {
                    "Name": "<Name of the conference/meeting>",
                    "Time": "<Time>",
                    "Location": "<Location>",
                    "Date": "<Date>",
                    "KeySpeakers": [
                        {
                            "SpeakerName": "<Speaker's name>",
                            "Topic": "<Related topic>"
                        },
                        {
                            "SpeakerName": "<Speaker's name>",
                            "Topic": "<Related topic>"
                        }
                    ],
                    "Organizers": [
                        {
                            "OrganizerName": "<Organizer's name>"
                        }
                    ],
                    "Agenda": "<Agenda of the conference/meeting>",
                    "PhoneNumber": "<Phone number>"
                },

            ]
        }
            """,
            },
            *base64_images,
        ],
        }
    ],
    )

    resp = response.choices[0].message.content
    json_data = resp.split("```json")[1].split("```")[0]
    data = json.loads(json_data)

    return data

def process_images_to_base64json(images):

    base64_images = []
    for img in images:
        image_buffer = BytesIO()
        img.save(image_buffer, format='JPEG')
        base64_image = base64.b64encode(image_buffer.getvalue()).decode('utf-8')
        base64_images.append({
                "type": "image_url",
                "image_url": {
                "url":  f"data:image/jpeg;base64,{base64_image}"
                },
            })
    
    
    return base64_images



st.title("GERMANY Scope: Intelligent PDF Data Extraction")
st.subheader("Convert PDF Documents into Multiple Excel Files with Ease")

api_key = st.text_input("Enter Authentication Key:", type="password")
if not authenticate_api_key(api_key):
    st.error("Invalid API key. Access denied.")
    st.stop()

uploaded_file = st.file_uploader("Upload your PDF", type=["pdf"], accept_multiple_files = True)

if uploaded_file is not None:
    
    
    # Convert PDF to images
    
    if uploaded_file:
        st.write("Processing PDF...")
        images = []
        for upl_file in uploaded_file:
            images += convert_from_bytes(upl_file.read(), poppler_path = poppler_path)
        
        # Process images to JSON
        base64_images = process_images_to_base64json(images)
        
        json_data = process_images_extract_json(base64_images)
        
        with st.spinner("Extracting Data..."):
            st.write("**Extraction Complete!**")
            
            # Extract and flatten data for DataFrame
            conference_rows = []
            for conf in json_data["ConferenceDetails"]:
                conference_rows.append({
                    "Name": conf["Name"],
                    "Time": conf["Time"],
                    "Location": conf["Location"],
                    "Date": conf["Date"],
                    "KeySpeakers": "; ".join(
                        [f"{speaker['SpeakerName']}" for speaker in conf["KeySpeakers"]]
                    ),
                    "Organizers": "; ".join([org["OrganizerName"] for org in conf["Organizers"]]),
                    "Agenda": conf["Agenda"],
                    "PhoneNumber": conf["PhoneNumber"]
                })

            # Convert to DataFrame
            df = pd.DataFrame(conference_rows)
            st.title("Conference Details")
            st.dataframe(df, use_container_width = True, height = 500, hide_index=True) 

        # create two columns
        # col1, col2 = st.columns(2)

        # with col1:
        #     st.title("PDF Images")
        #     st.image(images, width = 300)
        # with col2:
        #     with st.spinner("Extracting Data..."):
        #         st.write("**Extraction Complete!**")
                
        #         # Extract and flatten data for DataFrame
        #         conference_rows = []
        #         for conf in json_data["ConferenceDetails"]:
        #             conference_rows.append({
        #                 "Name": conf["Name"],
        #                 "Time": conf["Time"],
        #                 "Location": conf["Location"],
        #                 "Date": conf["Date"],
        #                 "KeySpeakers": "; ".join(
        #                     [f"{speaker['SpeakerName']} ({speaker['Topic']})" for speaker in conf["KeySpeakers"]]
        #                 ),
        #                 "Organizers": "; ".join([org["OrganizerName"] for org in conf["Organizers"]]),
        #                 "Agenda": conf["Agenda"]
        #             })

        #         # Convert to DataFrame
        #         df = pd.DataFrame(conference_rows)
        #         st.title("Conference Details")
        #         st.dataframe(df, use_container_width = True, height = 200, hide_index=True) 

        #         st.title("Conference Details JSON ")
        #         st.json(json_data, expanded=3)