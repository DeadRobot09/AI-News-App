import os
from datetime import datetime
import requests
from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from groq import Groq

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///news.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Setup Groq client with the API key
client = Groq(api_key="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")

# Database model for News
class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(120))
    author = db.Column(db.String(120))
    title = db.Column(db.String(120))
    description = db.Column(db.Text)
    url = db.Column(db.String(255))
    image_url = db.Column(db.String(255))
    published_at = db.Column(db.String(120))
    content = db.Column(db.Text)

    def __repr__(self):
        return f'<News {self.title}>'

with app.app_context():
    db.create_all()

def fetch_news():
    url = "https://newsapi.org/v2/top-headlines?country=in&apiKey=cee10f8e446142a29fb2ca5ae690cfcc"
    response = requests.get(url)
    return response.json()['articles'] if response.status_code == 200 else None

def generate_new_article(original_content):
    if not original_content:
        return "No content provided"
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": 'I am giving the news article to you please regenerate it. It should be rich in texts and should be seo friendly. and dont give headline just give content'},
            {"role": "user", "content": original_content}
        ],
        model="llama3-8b-8192",
    )
    return chat_completion.choices[0].message.content if chat_completion.choices else "Failed to generate content"

@app.route('/rewrite-news', methods=['GET'])
def rewrite_news():
    news_data = fetch_news()
    if news_data:
        News.query.delete()  # Clear existing news entries to avoid duplicates
        db.session.commit()
        for article in news_data:
            if article['content']:  # Only process articles with content
                new_content = generate_new_article(article['content'])
                article['content'] = new_content
                new_article = News(
                    source=article['source']['name'],
                    author=article['author'],
                    title=article['title'],
                    description=article['description'],
                    url=article['url'],
                    image_url=article['urlToImage'],
                    published_at=article['publishedAt'],
                    content=article['content']
                )
                db.session.add(new_article)
        db.session.commit()
        news_list = [{'id': news.id, 'title': news.title, 'published_at': news.published_at, 'image_url':news.image_url } for news in News.query.all()]
        return jsonify(news_list)
    else:
        return jsonify({"error": "Failed to fetch news"}), 500





@app.route('/')
def headlines():
    news_list = News.query.all()
    return render_template('headlines.html', news_list=news_list)

@app.route('/article/<int:news_id>')
def article(news_id):
    article = News.query.get(news_id)
    news_list = News.query.all()
    if article:
        return render_template('article.html', article=article, news_list=news_list)
    else:
        return 'Article not found', 404
    
if __name__ == '__main__':
    app.run(debug=True)
