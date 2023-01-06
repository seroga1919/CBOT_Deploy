import smtplib
import time
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException,NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# import re, logging
import re

# logging.basicConfig(filename="gig.log",
#                     filemode='a',
#                     format='%(asctime)s,%(name)s %(levelname)s %(message)s',
#                     datefmt='%H:%M:%S',
#                     level=logging.DEBUG)

class CraigScrapper:
    def __init__(self, sender_mail: str, password: str):
        # self.all_outputs = []
        self.all_titles = []
        self.password = password
        self.sender_mail = sender_mail

        with open("us_only_links.txt", "r") as file:
            self.all_us_sites = file.readlines()
        # print(self.all_us_sites)

        self.options = Options()
        self.options.add_argument("--headless") # Runs Chrome in headless mode.
        self.options.add_argument('--no-sandbox') # Bypass OS security model
        self.options.add_argument('--disable-gpu')  # applicable to windows os only
        self.options.add_argument('start-maximized') # 
        self.options.add_argument('disable-infobars')
        self.options.add_argument("--disable-extensions")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)

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

        negative_keywords = ["Walmart", "handyman", "handymen", "driver", "surrogates", "warehouse", "merchandiser", "appliance", "cleaner", "maid", "field inspector", "marketing research opportunity", "auditor", "model", "models", "merchandiser", "carpenters", "laborers", "painter", "drywall", "home health aid", "testers"]

        for i, site in enumerate(self.all_us_sites[int(currentUrlNo):]):
            # logging.info("===============   starting   ===============")
            # logging.info(site)
            # location_link = site.strip("\n").split("search")[0]
            location_link = site.strip("\n")
            search_url = location_link + "search/ggg"
            self.driver.get(url=search_url)
            print(search_url)
            # for query in result:
            for query in chunks:
                print(query)
                # logging.info(query)
                try:
                    time.sleep(1)
                    try: search = self.driver.find_element(By.XPATH, "//input[@placeholder='search gigs']")
                    except: search = self.driver.find_element(By.XPATH, "//input[@placeholder='search jobs']")
                    # search = self.driver.find_element(By.ID, "query")
                    # search = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.ID, 'query')))
                    search.clear()
                except NoSuchElementException:
                    print(f"Search element is not  found at {location_link}")
                    # logging.warning(f"Search element is not  found at {location_link}")
                else:
                    search.send_keys(query)
                    actions = ActionChains(self.driver)
                    actions.send_keys(Keys.ENTER)
                    actions.perform()
                    titles = []
                    try:
                        WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.result-title.hdrlnk")))
                        titles = self.driver.find_elements(By.CLASS_NAME, "titlestring") + self.driver.find_elements(By.CSS_SELECTOR, "a.result-title.hdrlnk")
                    except: 
                        # logging.warning(f"Title and link is not  found at {location_link}")
                        break
                        
                    temp = []
                    
                    for title in titles:
                        checkNegative = True
                        for negative_keyword in negative_keywords:
                            if negative_keyword.lower() in title.text.lower():
                                checkNegative = False
                                break
                        if (title.text not in self.all_titles) and checkNegative:
                            temp.append(title)
                            self.all_titles.append(title.text)

                    all_outputs = []
                    all_outputs += [f"{item.text}={item.get_attribute('href')}" for item in temp]
                    self.driver_1 = webdriver.Chrome(options=self.options)

                    for op in all_outputs:
                        link = op.split("=")[1]
                        title = op.split("=")[0]    
                        try:
                            self.driver_1.get(link)
                            time.sleep(1)
                            age =  self.driver_1.find_element(By.CSS_SELECTOR, "time.date.timeago").text
                            num = re.findall(r'\d+', age)[0]
                            if (not ("day" in age.lower() or "month" in age.lower())) and int(num) < 24:
                                posting_body = self.driver_1.find_element(By.ID, "postingbody")
                                e_body = posting_body.text + '\n\n'
                                content = [link, title, e_body]
                                self.mail(receiver_mail=receiver_mail, search_queries=search_queries_string, content=content)
                        except: 
                            # logging.error(f"Error in title : {title}")
                            pass

            with open('log.txt', 'w') as f:
                f.write(str(i+1))
                # logging.info(f"log_txt number: {i+1}")

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