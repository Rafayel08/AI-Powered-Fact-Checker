import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi as yta
from youtube_transcript_api.formatters import TextFormatter
import time
import nltk
import requests
from bs4 import BeautifulSoup
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
running=False
st.title('Video Transcriptor')
OPENAIKEY = "YOUR OPENAI KEY"
# st.write('Enter video url:')

urls={ #test URLS
 'VIDEO 1': 'https://www.youtube.com/watch?v=KWbOFmdVlUQ',
 'VIDEO 2': 'https://www.youtube.com/watch?v=346ZTxpCCgo',
 'VIDEO 3': 'https://www.youtube.com/watch?v=5LB9ZE_-03U',
 'VIDEO 4': 'https://www.youtube.com/watch?v=9tm4fmj4NUw',
 'VIDEO 5': 'https://www.youtube.com/watch?v=8WGHqRdt5FE',
 'VIDEO 6': 'https://www.youtube.com/watch?v=RfCQ1dCIXC4',
 'VIDEO 7': 'https://www.youtube.com/watch?v=WAdiFPFSBmU',
 'VIDEO 8': 'https://www.youtube.com/watch?v=b4L0dK7fJhE',
 'VIDEO 9': 'https://www.youtube.com/watch?v=JQW7wdyZv-c',
 'VIDEO 10': 'https://www.youtube.com/watch?v=06WDXGw4B80',
 'VIDEO 11': 'https://www.youtube.com/watch?v=-13GchmvQDs',
 'VIDEO 12': 'https://www.youtube.com/watch?v=LG_oRK8fVc8',
 'VIDEO 13': 'https://www.youtube.com/watch?v=KhqjI7w5JyE',
 'VIDEO 14': 'https://www.youtube.com/watch?v=Gxtsg8-0bw8'}
    # st.success("Done!")

# nltk.download('punkt')  # Download the punkt tokenizer data if not already installed

def extract_sentences(transcript):
    # Use NLTK's sentence tokenizer to split the transcript into sentences
    sentences = nltk.sent_tokenize(transcript)
    return sentences

def get_transcript(url):
  url=url.split('v=')[1]
  new_transcript=yta.get_transcript(url)
  formatter=TextFormatter()
  textformatted = formatter.format_transcript(new_transcript)
  textformatted=textformatted.replace('\n',' ')
  return textformatted

def get_youtube_video_publish_date(video_url):
    try:
        response = requests.get(video_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            date_element = soup.find('meta', itemprop='datePublished')
            if date_element:
                publish_date = date_element['content']
                return publish_date
    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")
    return None

import openai
openai.api_key=OPENAIKEY

def get_dates_from_transcript(url):
    transcript=get_transcript(url)
    dates=openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[
            {'role': 'system', 'content': "I will only return in the (month/day/year) format or I will return 'There are no dates mentioned in the transcript.'"},
            {'role': 'user', 'content': f'Get the lowest date of all the dates mentioned in the transcript of when events are happening in the format month/day/year. If you could not find any dates, return absolutely nothing. Do not even return anything. Here is the transcript: {transcript}'}
        ],
        temperature=0.0
    )
    
    if dates["choices"][0]["message"]['content']=='There are no dates mentioned in the transcript.':
        dates=get_youtube_video_publish_date(url)
        return str(dates)
    else:
        return str((dates["choices"][0]["message"]['content']))
    
def get_data(date_str, coin='BTC-USD'):
    date_format = '%Y-%m-%d'
    date_obj = datetime.strptime(date_str, date_format)
    delta = timedelta(days=14)
    date_14_days_before = date_obj - delta
    end_delta=timedelta(days=90)
    date_3_months_after=date_obj+end_delta
    df=yf.download(coin, start=date_14_days_before.strftime(date_format), end=date_3_months_after.strftime(date_format), interval='1d')
    return df



with st.sidebar:
    st.write('Put your url here')
    text_input=st.text_input('url')



    reformulate = st.radio(
        "Reformulate?",
        ('Yes', 'No')
        )   

    option = st.selectbox(
    'Example video selection',
    (list(urls.keys())))
    st.write(option)
    # st.write(urls[option])

    if st.button('run'):
        running=True   

with st.spinner('Loading...'):
    if running==True:
        my_bar = st.progress(0)
        try:
            transcript=get_transcript(text_input)
            date=get_dates_from_transcript(text_input)
            my_bar.progress(10)
        except Exception:
            transcript=get_transcript(urls[option])
            date=get_dates_from_transcript(urls[option])
            my_bar.progress(10)

        lowered_transcript=transcript.lower()
        list_of_coins=[]
        dataframes_of_coins=[]
        if 'bitcoin' or 'btc' in transcript:
            list_of_coins.append('BTC-USD')
        if 'altcoin' or 'alt' in transcript:
            pass
            

        df=get_data(date, 'BTC-USD')


        if reformulate == 'Yes':
            remade_transcript = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages = [{"role": "user", "content": "Rewrite this but with the periods placed when the sentences end. Also reformulate the text to fix any errors in the transcription:" + str(transcript)}]
            )
            transcript=remade_transcript["choices"][0]["message"]['content']
            my_bar.progress(30)


        claims=openai.ChatCompletion.create(
                    model='gpt-3.5-turbo',
                    messages = [
                        # {"role": "system", "content": f"I will print out in this format: claim; claim; claim; etc."},
                        {"role": "user", "content": f"Get every claim in this transcript: {transcript}"}
                        # {"role": "user", "content": f"Get every claim and prediction in this transcript and seperate each claim that you write down by a semicolon: {transcript}"}
                        ],
                    temperature=0.0
                    )
        my_bar.progress(50)

        claims=claims["choices"][0]["message"]['content']

        claims=claims.split('\n')
        for claim in claims:
            claim=claim[3:]

        amount_of_claims=len(claims)
        amount_to_progress=int(49/amount_of_claims)
        current_progress=50

        format={
            'Symbol': 'Ticker symbol',
            'claim': 'the claim',
            'sentiment': 'Bullish/Bearish/NA',
            'validation': 'True or False',
            'Analysis': 'analysis'
        }

        for i, claim in enumerate(claims):
            # st.write(claim)
            # st.write(i)
            st.markdown("""---""") 
            check=openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages = [
                    {'role': 'system', 'content': f'''Act as a claim extractor.
                     
                        Please organize the provided information about the cryptocurrency predictions using the following format:

                        {i+1}.'[Ticker Symbol]': (Claim)
                        Sentiment: (Bullish/Bearish/NA)
                        Validation: (True/False)
                        Analysis: (Analysis)

                        Make sure to follow these guidelines:
                        - Place the ticker symbol (crypto currency symbol) in brackets, on the same line as the claim.
                        - The claim is the prediction made about the cryptocurrency's direction and prices. Write it outside the brackets and right next to the ticker symbol.
                        - Specify whether the claim suggests a bullish, bearish sentiment, or no sentiment at all.
                        - Indicate if the claim's validation result is true or false.
                        - Provide a comprehensive analysis that delves into the claim, sentiment, and reasons for its accuracy or inaccuracy.

                        You can use the data from the given dataframe containing price information to support your predictions.

                    '''},               

                    {"role": "user", "content": f'''Check to see if this claim was true by looking at this price data. Price Data: {df}. And here is the claim: {claim}. You can also use the date of around when the video was made as well: {date}'''}
                    ],
                    temperature=0.2
                )
            check=check["choices"][0]["message"]['content']
            st.write(check)
            my_bar.progress(current_progress+amount_to_progress)
            current_progress+=amount_to_progress

        my_bar.progress(100)
        time.sleep(1)
        my_bar.empty()

        st.success('Done')
