from flask import Flask ,render_template,url_for,request, redirect,session
import pickle
import numpy as np 
import requests
import mysql.connector
from bs4 import BeautifulSoup
import nltk 
import pandas as pd
import os
popular_df=pickle.load(open('popular.pkl','rb'))
pt= pickle.load(open('pt.pkl','rb'))
books= pickle.load(open('books.pkl','rb'))
similarity_score= pickle.load(open('similarity_scores.pkl','rb'))
app = Flask(__name__)
app.secret_key=os.urandom(24)
conn=mysql.connector.connect(host='localhost',user='root',password='',database='raja')
cursor=conn.cursor()
def get_wiki_content(url):
    req_obj = requests.get(url)
    text = req_obj.text
    soup = BeautifulSoup(text)
    all_paras = soup.find_all("p")
    wiki_text = ''
    for para in all_paras:
        wiki_text += para.text 
    return wiki_text

def top10_sent(url):
    required_text = get_wiki_content(url)
    stopwords = nltk.corpus.stopwords.words("english")
    sentences = nltk.sent_tokenize(required_text)
    words = nltk.word_tokenize(required_text)
    word_freq = {}
    for word in words:
        if word not in stopwords:
            if word not in word_freq:
                word_freq[word] = 1
            else:
                word_freq[word] += 1

    max_word_freq = max(word_freq.values())
    for key in word_freq.keys():
        word_freq[key] /= max_word_freq

    sentences_score = []
    for sent in sentences:
        curr_words = nltk.word_tokenize(sent)
        curr_score = 0
        for word in curr_words:
            if word in word_freq:
                curr_score += word_freq[word]
        sentences_score.append(curr_score)

    sentences_data = pd.DataFrame({"sent":sentences, "score":sentences_score})
    sorted_data = sentences_data.sort_values(by = "score", ascending = False).reset_index()

    top10_rows = sorted_data.iloc[0:30,:]

    #top_10 = list(sentences_data.sort_values(by = "score",ascending = False).reset_index().iloc[0:11,"sentences"])
    return " ".join(list(top10_rows["sent"]))


@app.route('/raja' , methods = ["GET", "POST"])
def hol():
    if request.method == "POST":
        url = request.form.get("url")
        url_content = top10_sent(url)
        return url_content
    return render_template("home.html")


@app.route("/")
def hello_world():
      return render_template("index.html",
                           book_name= list(popular_df['Book-Title'].values),
                           author= list(popular_df['Book-Author'].values),
                           image= list(popular_df['Image-URL-M'].values),
                           votes= list(popular_df['num_ratings'].values),
                           ratings= list(popular_df['avg_rating'].values),
                           )


@app.route('/recommend')
def recommend():
   return render_template('recommend.html')

@app.route('/logout')
def logout():
   session.pop('username')
   return redirect('/')


@app.route('/aboutus')
def aboutus_ui():
   return render_template('aboutus.html')

@ app.route('/login')
def log():
   return render_template('login.html')

@ app.route('/register')
def reg():
   return render_template('register.html')

@ app.route('/r_velidation' ,methods=['POST'])
def vel():
   email=request.form.get('email')
   password=request.form.get('password')
   cursor.execute("""SELECT * FROM  `rajan` WHERE `email` Like '{}' AND `password` Like '{}'""".format(email,password))
   rajan=cursor.fetchall()
   if len(rajan)>0:
      session['userid']=rajan[0][0]

      return redirect('/')
   else:
      return redirect('login.html')

@ app.route('/registration' ,methods=['POST'])
def raj():
   name=request.form.get('username')
   email=request.form.get('email')
   password=request.form.get('password')
   cursor.execute("""INSERT INTO `rajan`(`userid`,`name`,`email`,`password`) VALUES
   (NULL,'{}','{}','{}')""".format(name,email,password))
   conn.commit()
   return 'User registered successfully'


@app.route('/contact us')
def contactus():
   return render_template('contact us.html')


@app.route('/recommend_books', methods=['post'])
def recommend2():
    user_input = request.form.get('user_input')
    index = np.where(pt.index==user_input)[0][0]
    similar_items = sorted(list(enumerate(similarity_score[index])),key=lambda x:x[1],reverse=True)[1:5]
    
    data = []
    for i in similar_items:
        item = []
        temp_df = books[books['Book-Title'] == pt.index[i[0]]]
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Title'].values))
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Author'].values))
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Image-URL-M'].values))
        
        data.append(item)

    print(data)
    return render_template('recommend.html',data=data)


if __name__=="__main__":
 app.run(debug=True)