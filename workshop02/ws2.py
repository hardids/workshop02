from flask import Flask, render_template, request, redirect, abort, session, jsonify
import json, re, random, datetime, requests, os, pymysql
from datetime import date, timedelta
from bs4 import BeautifulSoup
from selenium import webdriver

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config['ENV'] = 'development'
app.config['DEBUG'] = True
app.secret_key = 'angel'

#DB 이용
db = pymysql.connect(
    user='root',
    passwd='911004',
    host='localhost',
    db='ws2',
    charset='utf8',
    cursorclass=pymysql.cursors.DictCursor
)

@app.route("/login", methods=['GET', 'POST'])
def login():
    message = ""
    
    if 'id' in session:
        return redirect("/")    
    
    if request.method == 'POST':
        cursor = db.cursor()
        cursor.execute(f"""
            select id, name, password from mymember 
            where id = '{request.form['id']}'""")
        user = cursor.fetchone()
        print(user)
        
        if user is None:
            message = "회원이 아닙니다."
        else:
            cursor.execute(f"""
            select id, name, password from mymember 
            where id = '{request.form['id']}' and 
                  password = SHA2('{request.form['password']}', 256)""")
            user = cursor.fetchone()
            
            if user is None:
                message = "패스워드를 확인해 주세요"
            else:
                # Flask Session, template 활용
                session['id'] = user
                print(session['id']['id'])
                return redirect("/")
    
    return render_template('login.html', 
                           message=message)



@app.route("/new", methods=['GET', 'POST'])
def newmember():
    message = ""

    if request.method == 'POST':
        cursor = db.cursor()
        cursor.execute(f"""select id from mymember where id = '{request.form['id']}'""")
        checkuser = cursor.fetchone()

        if checkuser:
            return render_template('login.html',
                           title = "Sign UP",
                           message = "ID 중복입니다. 다른 ID를 입력해주세요"
                           )

        sql = f"""insert into mymember (id, name, password) 
            values ('{request.form['id']}', '{request.form['name']}', SHA2('{request.form['password']}', 256))"""

        cursor.execute(sql)
        print(sql)
        db.commit()
        user = cursor.fetchone()
        return redirect("/login")
        print(user)
        
    
    return render_template('new.html',
                           title = "Sign UP"
                           )




@app.route("/", methods=['GET', 'POST'])
def index():
    if 'id' in session:
        content = 'Hello ' + session['id']['id']
        return render_template('index.html',
                          content = content)
    return 'You Must LOGIN for Using Service'

@app.route('/logout')
def logout():
    session.pop('id', None)
    return redirect('/login')


@app.route('/crawler/news')
def crawler_news():
    if 'id' not in session:
        return 'You Must LOGIN for Using Service'
    
    driver = webdriver.Chrome('chromedriver')
    url = "https://news.naver.com"
    driver.get(url)
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    news_headers_raw = soup.select("ul.mlist2 a strong") #tree 구조를 공부해야겠네...
    news_headers = []
    
    for i in range(len(news_headers_raw)):
        news_headers.append(news_headers_raw[i].text)
    
    print(dir(news_headers_raw[0]))
    print(news_headers_raw[0].text, len(news_headers_raw))
    return render_template('crawler.html',
                           theme = 'Selenium, BeautifulSoup 활용 Crawling',
                           newsheader = news_headers)


@app.route('/crawler/news_author')
def crawler_news_author_recent():
    if 'id' not in session:
        return 'You Must LOGIN for Using Service'
    
    url = "https://news.naver.com"

    res = requests.get(url)
    soup = BeautifulSoup(res.content, 'html.parser')
    news_headers_raw = soup.select('ul.mlist2 a strong')
    news_headers_pick = soup.select('ul.mlist2 a')
    news_headers = []
    
    for i in range(len(news_headers_raw)):
        news_headers.append(news_headers_raw[i].text)    
    
    #regex를 활용한 추출
    emailregex = re.compile('(?!Article)[a-zA-Z0-9+-_.]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
    emailadd = []
    
    for tag in news_headers_pick:
        res2 = requests.get(tag['href'], verify=False)
        new_soup = BeautifulSoup(res2.content, 'html.parser')
        text = str(new_soup)
        emailadd.append(emailregex.findall(text))
        
    news_title = news_headers
    
    lists = [[i, j] for i, j in zip(news_title, emailadd)]
    print("*" * 20)
    print(lists)
    
    #for i in list(temp)
    
    return render_template('check_author.html',
                          theme = 'regex test',
                           lists = lists)
#                           news_title = news_title,
#                           email_add = emailadd)


#Selenium으로 안불러오니까 다중 호출시 SSL Socket 에러남

@app.route('/crawler/news_author/<word>')
def crawler_news_author(word):
    if 'id' not in session:
        return 'You Must LOGIN for Using Service'
    
    url = f"https://search.naver.com/search.naver"
    query = {
        "where": "news",
        "ie" "utf8"
        "sm": "nws_hty",
        "query": word
    }
    res = requests.get(url, params=query)
    soup = BeautifulSoup(res.content, 'html.parser')
    news_headers_raw = soup.select('ul.type01 li dl dt a')

    #regex를 활용한 추출
    # emailregex = re.compile('(?!Article).[a-zA-Z0-9+-_.]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
    emailregex = re.compile('([a-zA-Z0-9+-.]+@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-.]+)*\.[a-zA-Z-.]{2,})')
    #    emailregex = re.compile('[a-zA-Z0-9+-_.]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
    emailadd = []
    news_title = []
    
    for tag in news_headers_raw:
        news_title.append(str(tag['title']))
        res2 = requests.Session().get(tag['href'], verify=False)
        new_soup = BeautifulSoup(res2.content, 'html.parser')
        # print("*" * 20)
        # print(new_soup.body.get_text().replace('\n', ''))
        # [e[0] for e in emailregex.findall(new_soup.body.get_text())]
        emailadd.append([e[0] for e in emailregex.findall(new_soup.body.get_text())])

    #for i in list(temp)
    lists = [[i, j] for i, j in zip(news_title, emailadd)]    
    return render_template('check_author.html',
                          theme = 'regex test',
                          lists = lists)
#                         news_title = news_title,
#                         email_add = emailadd)

@app.route('/submit', methods = ['GET', 'POST'])
def news_redirect():
    if 'id' not in session:
        return 'You Must LOGIN for Using Service'
    print(request.form['word'])
    return redirect(f"/crawler/news/{request.form['word']}") #f = variable formatting
                          
                           
                           
'''
#강사님 Style    

    for tag in news_headers_raw:
        
        requests.get(tag['href']))       
        new_soup = BeautifulSoup(driver.page_source, 'html.parser')


#regex
    
 


#code for finding text header

    for i in range(len(news_headers_raw)):
        news_headers.append(news_headers_raw[i].text)
    
    print(dir(news_headers_raw[0]))
    print(news_headers_raw[0].text, len(news_headers_raw))

'''
@app.route('/submitauthor', methods = ['GET', 'POST'])
def news_redirect_author():
    if 'id' not in session:
        return 'You Must LOGIN for Using Service'
    print(request.form['word'])
    return redirect(f"/crawler/news_author/{request.form['word']}") #f = variable formatting



###Selenium, Requests 활용 Crawling and BeautifulSoup을 활용한 Parsing
@app.route('/crawler/news/<word>', methods = ['GET', 'POST'])
def crawler_word(word):
    
    if 'id' not in session:
        return 'You Must LOGIN for Using Service'
    
    url = f"https://search.naver.com/search.naver"
    query = {
        "where": "news",
        "ie" "utf8"
        "sm": "nws_hty",
        "query": word
    }
    res = requests.get(url)

    driver = webdriver.Chrome('chromedriver')
    driver.implicitly_wait(3)
    driver.get(url)
    driver.page_source
    
    response = requests.get(url, params=query)
    soup = BeautifulSoup(response.content, 'html.parser')
    news_headers_raw = soup.select('ul.type01 li dl dt a') #list
    news_headers =[]
    
    for i in range(len(news_headers_raw)):
        news_headers.append(str(news_headers_raw[i]['title']))
    
    #print(news_headers_raw[0]['title'])

    return render_template('crawler.html',
                           theme = 'Selenium, Request, BeautifulSoup 활용 Crawling',
                           newsheader = news_headers)    
    
app.run(port=1234)