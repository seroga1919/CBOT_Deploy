from flask import Flask, request
from craig import CraigScrapper

app = Flask(__name__)

sender_mail = "arclightcl@gmail.com"
password = 'pqnkqxmewfjkskzf'

craig = CraigScrapper(sender_mail=sender_mail, password=password)
scrapper = True

@app.route('/start', methods=['GET'])
def start():
    global scrapper
    if request.method == 'GET':
        try:
            with open('log.txt', 'r') as f:
                currentUrlNo = f.read()
        except: currentUrlNo = 0
        
        receiver_mail = "arclightcl@gmail.com"
        print(receiver_mail)

        scrapper = True
        while scrapper:
            craig.scrapSend(receiver_mail=receiver_mail, currentUrlNo=currentUrlNo)
            # craig.mail(receiver_mail=receiver_mail, search_queries=search_queries, link=links)
        return "OK", 200

@app.route('/stop', methods=['GET'])
def stop():
    global scrapper
    scrapper = False
    return "OK",200

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
