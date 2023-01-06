from time import sleep
import smtplib
import time
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import re
import requests
from bs4 import BeautifulSoup as BS
from datetime import datetime, timedelta
from nltk.stem import WordNetLemmatizer
import nltk
nltk.download('all')

cookies = {
    'cl_b': '4|4d406241f79ad3e16557ca72f1ac4d3eadecf926|1672671326kGhKI',
    'cl_tocmode': 'ggg%3Alist',
}


headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Sec-GPC': '1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Brave";v="108"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

NEGATIVE_KEYWORDS = ["Walmart", "handyman", "handymen", "driver", "surrogate", "warehouse", "merchandiser", "appliance", "cleaner", "maid", "field inspector", "marketing research opportunity", "auditor", "model", "merchandiser", "carpenter", "laborer", "painter", "drywall", "home health aid", "tester"]

def lemmatize_word(word):
    lemmatizer = WordNetLemmatizer()
    return lemmatizer.lemmatize(word)
    
    
def filter_negative_results(all_results):
    positive_results = []
    for result in all_results:
        for keyword in NEGATIVE_KEYWORDS:
            if len(keyword.split(' '))>1:
                if keyword.lower() in result['title']:
                    break
                else:
                    positive_results.append(result)
                    break
            if keyword.lower() in list(map(lemmatize_word, result['title'].lower().split(' '))):
                break
        else:
            positive_results.append(result)
    return positive_results
    
def filter_time(all_results):
    new_results = []
    for result in all_results:
        y,m,d = list(map(int, result['date'].split(' ')[0].split('-')))
        current_date = datetime.now()
        posted_date = datetime(y,m,d)
        if (current_date - posted_date).days < 4:
            new_results.append(result)
    return new_results
    
    
def get_all_links(main_link, query):
    params = {
    'query': query,
    'is_paid': 'all',
    }

    response = requests.get(f'{main_link}search/ggg', params=params, cookies=cookies, headers=headers)
    print(response)
    soup = BS(response.text)
    all_results = [{'title': _.text.strip(), 'link': _.a['href'], 'date':_.parent.time['datetime']} for _ in soup.find_all('h3',{'class':'result-heading'})]
    positive_results = filter_negative_results(all_results)
    new_positive_results = filter_time(positive_results)
    return new_positive_results
    
    
def get_data(result):
    response = requests.get( result['link'],
                            cookies=cookies,
                            headers=headers,)
    soup = BS(response.text)
    body = soup.find('section',{'id':'postingbody'}).text.strip() + '\n\n'
    return [result['link'], result['title'], body]

class CraigScrapper:
    def __init__(self, sender_mail: str, password: str):
        # self.all_outputs = []
        self.all_titles = []
        self.password = password
        self.sender_mail = sender_mail

        with open("us_only_links.txt", "r") as file:
            self.all_us_sites = file.readlines()
        # print(self.all_us_sites)

    def scrapSend(self, receiver_mail=str, currentUrlNo=str):
        MAX_QUERY_LENGTH = 100
        search_queries = ["development","HTML","Javascript","PHP","Laravel","Website","Developer","Programmer","Coder","Marketing","dev","design","software","Application","Mobile","Android", "computer vision", "deep learning", "youtube", "API", "Security Lead", "trading", "Logo", "Data Entry", "SalesForce", "WooCommerce", "Marketing", "Digital Marketing", "Financial Software Reporting", "IT", "Email Marketing", "Motion Graphics"]
        formatted_queries = [f'"{v.strip()}"' for v in search_queries]
        search_queries_string = "|".join(formatted_queries)
        
        if len(search_queries_string) > MAX_QUERY_LENGTH:
            n = int(len(search_queries_string)/MAX_QUERY_LENGTH)
            chunks = [None]*(n+1)
            start_index = 0
            
            for i in range(n):
                if start_index + MAX_QUERY_LENGTH >= len(search_queries_string): 
                    chunks[i] = search_queries_string[start_index:]
                    break
                if search_queries_string[start_index + MAX_QUERY_LENGTH] == "|":
                    chunks[i] = search_queries_string[start_index:MAX_QUERY_LENGTH*(i+1)]
                    pipe_index = MAX_QUERY_LENGTH + start_index
                else:
                    for j in range(1,100):
                        if search_queries_string[start_index + MAX_QUERY_LENGTH+j] == "|":
                            pipe_index = MAX_QUERY_LENGTH + start_index + j
                            break
                
                chunks[i] = search_queries_string[start_index:pipe_index]
                start_index = pipe_index + 1
            chunks = [v for v in chunks if v != None]
        else: chunks = [search_queries_string]

        for i, site in enumerate(self.all_us_sites[int(currentUrlNo):]):
            location_link = site.strip("\n")
            print(location_link)
            for query in chunks:
                # print(query)
                try:
                    all_outputs = get_all_links(location_link, query)
                    sleep(1)
                except Exception as e:
                    print(e)
                    continue
                
                for op in all_outputs:
                    content = get_data(op)
                    sleep(1)
                    # final_results.append(content)
                    self.mail(receiver_mail=receiver_mail, search_queries=search_queries_string, content=content)

            with open('log.txt', 'w') as f:
                f.write(str(i+1))
                # logging.info(f"log_txt number: {i+1}")
        return None

    def mail(self, receiver_mail: str, search_queries: list, content:list):
        
        link, title, e_body = content
        
        # instance of MIMEMultipart
        msg = MIMEMultipart()

        # storing the senders email address
        msg['From'] = self.sender_mail

        # storing the receivers email address
        msg['To'] = receiver_mail

        # storing the subject
        msg['Subject'] = title

        # string to store the body of the mail
        # e_head = "Scrape Result" + "\n\n"
        querylist = "Search from: " + search_queries
        pLink = "from Craiglist: " + link + "\n\n"
        email_body = e_body + pLink + querylist

        msg.attach(MIMEText(email_body, 'plain'))

        # creates SMTP session
        s = smtplib.SMTP('smtp.gmail.com', '587')

        # start TLS for security
        s.starttls()

        # Authentication
        s.login(self.sender_mail, self.password)

        # Converts the Multipart msg into a string
        text = msg.as_string()

        # sending the mail
        s.sendmail(self.sender_mail, receiver_mail, text)

        # terminating the session
        s.quit()
        # logging.info(f"Msg sent in {link}")
        
        time.sleep(1)