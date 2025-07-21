from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify
import pandas as pd
from transformers import pipeline
from slack_sdk import WebClient
from wordcloud import WordCloud
import io
import base64
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import os
import imaplib
import email

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for flash to work
emails = []  # Global variable to store email list

# Initialize sentiment and emotion analyzers
try:
    emotion_analyzer = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base", top_k=None)
except Exception as e:
    print(f"Failed to load emotion analyzer: {str(e)}")
    emotion_analyzer = None
    try:
        emotion_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
        print("Using fallback sentiment model")
    except Exception as e:
        print(f"Failed to load fallback sentiment analyzer: {str(e)}")
        emotion_analyzer = None

# Mock Slack client
slack_client = WebClient(token="xoxb-9219054992275-9248518081216-FashwxCcRApefkfpIV5rIIuz")
alert_log = []

# Generate word cloud
def generate_wordcloud(text, emotion):
    try:
        wordcloud = WordCloud(width=400, height=200, background_color="white").generate(text)
        img = io.BytesIO()
        wordcloud.to_image().save(img, format="PNG")
        img.seek(0)
        return base64.b64encode(img.getvalue()).decode()
    except:
        return None

# Send email report
def send_email_report(sentiment_counts, top_issues):
    try:
        msg = MIMEText(render_template("email_report.html", sentiment_counts=sentiment_counts, top_issues=top_issues), "html")
        msg["Subject"] = "Weekly Sentiment Watchdog Report"
        msg["From"] = "shweta.22311909@viit.ac.in"
        msg["To"] = "shwetaumbrajkaar11@gmail.com"
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login("shweta.22311909@viit.ac.in", "voffticmkzojxhhz")
            server.send_message(msg)
        alert_log.append("Email report sent successfully")
    except Exception as e:
        alert_log.append(f"Email report failed: {str(e)}")

# Analyze tickets
def analyze_tickets(filters=None):
    try:
        df = pd.read_csv("tickets.csv") if os.path.exists("tickets.csv") else pd.DataFrame()
        if emotion_analyzer and not df.empty:
            if "emotion-english" in emotion_analyzer.model.name_or_path:
                df["emotions"] = df["text"].apply(lambda x: emotion_analyzer(x)[0][0]["label"])
                df["sentiment"] = df["emotions"].apply(lambda x: "POSITIVE" if x in ["joy", "surprise"] else "NEGATIVE" if x in ["anger", "sadness", "fear"] else "NEUTRAL")
            else:
                df["sentiment"] = df["text"].apply(lambda x: emotion_analyzer(x)[0]["label"].upper())
                df["emotions"] = df["sentiment"]
        else:
            df["sentiment"] = "UNKNOWN"
            df["emotions"] = "UNKNOWN"
        
        if filters:
            if "sentiment" in filters and filters["sentiment"]:
                df = df[df["sentiment"] == filters["sentiment"]]
            if "date" in filters and filters["date"]:
                df = df[pd.to_datetime(df["timestamp"], format="%d-%m-%Y %H:%M").dt.date == pd.to_datetime(filters["date"]).date()]
        
        df["hour"] = pd.to_datetime(df["timestamp"], format="%d-%m-%Y %H:%M").dt.floor("h")
        sentiment_counts = df["sentiment"].value_counts().to_dict()
        emotion_counts = df["emotions"].value_counts().to_dict()
        sentiment_counts = {"POSITIVE": int(sentiment_counts.get("POSITIVE", 0)), "NEGATIVE": int(sentiment_counts.get("NEGATIVE", 0)), "NEUTRAL": int(sentiment_counts.get("NEUTRAL", 0))}
        emotion_counts = {k: int(v) for k, v in emotion_counts.items()}
        
        df["department"] = df["ticket_id"].apply(lambda x: "Team A" if x % 2 == 0 else "Team B")
        dept_sentiment = df.groupby(["department", "sentiment"]).size().unstack().fillna(0).to_dict()
        
        happiest_day = pd.to_datetime(df[df["sentiment"] == "POSITIVE"]["timestamp"], format="%d-%m-%Y %H:%M").dt.date.value_counts().idxmax() if not df[df["sentiment"] == "POSITIVE"].empty else "N/A"
        top_agent = df[df["sentiment"] == "POSITIVE"]["department"].value_counts().idxmax() if not df[df["sentiment"] == "POSITIVE"].empty else "N/A"
        
        wordclouds = {}
        for emotion in df["emotions"].unique():
            text = " ".join(df[df["emotions"] == emotion]["text"].tolist())
            wordclouds[emotion] = generate_wordcloud(text, emotion)
        
        negative_count = df[df["sentiment"] == "NEGATIVE"].groupby("hour").size()
        spike = negative_count[negative_count > 3]
        if not spike.empty and f"Negative sentiment spike: {spike.iloc[-1]} negative tickets at {spike.index[-1]}" not in alert_log:
            alert_log.append(f"Negative sentiment spike: {spike.iloc[-1]} negative tickets at {spike.index[-1]}")
            try:
                slack_client.chat_postMessage(channel="#sentiment-alerts", text=alert_log[-1])
            except Exception as e:
                alert_log.append(f"Slack alert failed: {str(e)}")
        
        top_issues = df[df["sentiment"] == "NEGATIVE"]["text"].str.lower().str.findall(r"\b(login|refund|slow|crash)\b").explode().value_counts().head(3).to_dict() if not df.empty else {}
        
        return df, sentiment_counts, emotion_counts, dept_sentiment, happiest_day, top_agent, wordclouds, alert_log
    except Exception as e:
        print(f"Error in analyze_tickets: {str(e)}")
        return pd.DataFrame(), {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0}, {}, {}, "N/A", "N/A", {}, [f"Error processing tickets: {str(e)}"]

# Fetch and analyze a single email
def fetch_and_analyze_email(body=None):
    try:
        if body:
            emotion = emotion_analyzer(body)[0][0]["label"] if emotion_analyzer and "emotion-english" in emotion_analyzer.model.name_or_path else emotion_analyzer(body)[0]["label"].upper() if emotion_analyzer else "UNKNOWN"
            return "Generated Subject", body, emotion
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login("shweta.22311909@viit.ac.in", "voffticmkzojxhhz")
        mail.select("inbox")
        status, data = mail.search(None, "ALL")
        if data[0]:
            latest_email_id = data[0].split()[-1]
            status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
            raw_email = msg_data[0][1]
            email_message = email.message_from_bytes(raw_email)
            subject = email_message["Subject"]
            body = ""
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        break
            else:
                body = email_message.get_payload(decode=True).decode()
            max_length = 512 * 4
            body = body[:max_length] if len(body) > max_length else body
            emotion = emotion_analyzer(body)[0][0]["label"] if emotion_analyzer and "emotion-english" in emotion_analyzer.model.name_or_path else emotion_analyzer(body)[0]["label"].upper() if emotion_analyzer else "UNKNOWN"
            return subject, body, emotion
        return None, None, None
    except Exception as e:
        print(f"Error fetching email: {str(e)}")
        return None, None, None

# Fetch and analyze all emails
def fetch_and_analyze_emails():
    global emails
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login("shweta.22311909@viit.ac.in", "voffticmkzojxhhz")
        mail.select("inbox")
        status, data = mail.search(None, "ALL")
        emails = []
        if data[0]:
            for email_id in data[0].split():
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                raw_email = msg_data[0][1]
                email_message = email.message_from_bytes(raw_email)
                subject = email_message["Subject"]
                body = ""
                if email_message.is_multipart():
                    for part in email_message.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = email_message.get_payload(decode=True).decode()
                max_length = 512 * 4
                body = body[:max_length] if len(body) > max_length else body
                emotion = emotion_analyzer(body)[0][0]["label"] if emotion_analyzer and "emotion-english" in emotion_analyzer.model.name_or_path else emotion_analyzer(body)[0]["label"].upper() if emotion_analyzer else "UNKNOWN"
                sentiment = "POSITIVE" if emotion in ["joy", "surprise"] else "NEGATIVE" if emotion in ["anger", "sadness", "fear"] else "NEUTRAL"
                emails.append({"subject": subject, "body": body, "emotion": emotion, "sentiment": sentiment, "status": "pending"})
        else:
            mock_emails = [
                {"subject": "Great Service!", "body": "I’m so happy with the quick resolution!", "emotion": "joy", "sentiment": "POSITIVE", "status": "replied"},
                {"subject": "Amazing Support", "body": "Your team was fantastic!", "emotion": "joy", "sentiment": "POSITIVE", "status": "pending"},
                {"subject": "Urgent Refund", "body": "Frustrated with the delay!", "emotion": "anger", "sentiment": "NEGATIVE", "status": "replied"},
                {"subject": "Slow Service", "body": "Too slow, upset!", "emotion": "sadness", "sentiment": "NEGATIVE", "status": "pending"}
            ]
            emails = mock_emails
        return emails
    except Exception as e:
        print(f"Error fetching emails: {str(e)}")
        return [
            {"subject": "Great Service!", "body": "I’m so happy with the quick resolution!", "emotion": "joy", "sentiment": "POSITIVE", "status": "replied"},
            {"subject": "Amazing Support", "body": "Your team was fantastic!", "emotion": "joy", "sentiment": "POSITIVE", "status": "pending"},
            {"subject": "Urgent Refund", "body": "Frustrated with the delay!", "emotion": "anger", "sentiment": "NEGATIVE", "status": "replied"},
            {"subject": "Slow Service", "body": "Too slow, upset!", "emotion": "sadness", "sentiment": "NEGATIVE", "status": "pending"}
        ]

# Generate AI reply
def generate_ai_reply(emotion):
    replies = {
        "anger": {"text": "“Hi, we understand your frustration. We’re escalating your refund request and will update you within 24 hours.”"},
        "sadness": {"text": "“Hi, we’re sorry you’re upset. We’re investigating and will resolve this soon.”"},
        "joy": {"text": "“Hi, we’re glad you’re happy! We’ll follow up if needed.”"},
        "surprise": {"text": "“Hi, we’re excited to hear from you! Your request is being processed.”"},
        "neutral": {"text": "“Hi, thanks for your message. We’ll get back to you shortly.”"},
        "UNKNOWN": {"text": "“Hi, we’ve received your message. We’ll review and respond soon.”"}
    }
    return replies.get(emotion.lower(), replies["neutral"])

# Send reply email
def send_reply_email(subject, reply_text, to_email, email_id):
    try:
        msg = MIMEText(reply_text, "plain")
        msg["Subject"] = f"Re: {subject}"
        msg["From"] = "shweta.22311909@viit.ac.in"
        msg["To"] = to_email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login("shweta.22311909@viit.ac.in", "voffticmkzojxhhz")
            server.send_message(msg)
        return "Replied"
    except Exception as e:
        return f"Error sending reply: {str(e)}"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    filters = {}
    if request.method == "POST":
        filters["sentiment"] = request.form.get("sentiment")
        filters["date"] = request.form.get("date")
    df, sentiment_counts, emotion_counts, dept_sentiment, happiest_day, top_agent, wordclouds, alerts = analyze_tickets(filters)
    return render_template("dashboard.html", data=df.to_dict(orient="records") if not df.empty else [], counts=sentiment_counts, 
                          emotions=emotion_counts, dept_sentiment=dept_sentiment, happiest_day=happiest_day, 
                          top_agent=top_agent, wordclouds=wordclouds, alerts=alerts)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files["file"]
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)
        if file and file.filename.endswith(".csv"):
            df = pd.read_csv(file)
            df.to_csv("tickets.csv", index=False)
            flash("File uploaded successfully!")
            return redirect(url_for("dashboard"))
    return render_template("upload.html")

@app.route("/send_email", methods=["POST"])
def send_email():
    df, sentiment_counts, emotion_counts, _, _, _, _, alert_log = analyze_tickets()
    top_issues = df[df["sentiment"] == "NEGATIVE"]["text"].str.lower().str.findall(r"\b(login|refund|slow|crash)\b").explode().value_counts().head(3).to_dict() if not df.empty else {}
    send_email_report(sentiment_counts, top_issues)
    return {"status": "Email triggered", "alerts": alert_log}

@app.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")

@app.route("/get_response", methods=["POST"])
def get_response():
    user_message = request.json.get("message")
    responses = {
        "how to use?": "Upload a CSV file via 'Upload CSV Report' and view insights on 'View Dashboard'!",
        "what is this?": "Customer Sentiment Watchdog analyzes emotions from text, speech, or chat.",
        "help": "Ask 'How to use?' or 'What is this?' for guidance!",
        "where is dashboard?": "Click 'View Dashboard' or visit http://127.0.0.1:5000/dashboard!",
        "how to upload?": "Click 'Upload CSV Report' and select your CSV file.",
        "contact support": "Email Shweta at shwetaumbrajkaar11@gmail.com or use the chatbot."
    }
    return jsonify({"response": responses.get(user_message.lower(), "Sorry, I didn’t understand. Try 'Help'!")})

@app.route("/fetch_email", methods=["POST"])
def fetch_email():
    data = request.json or {}
    subject, body, emotion = fetch_and_analyze_email(data.get("body"))
    if subject and body:
        reply_suggestion = generate_ai_reply(emotion)
        return {"status": "Email fetched", "subject": subject, "body": body, "emotion": emotion, "reply": reply_suggestion}
    return {"status": "No email fetched", "subject": "", "body": "", "emotion": "", "reply": {"text": "No email to analyze."}}

@app.route("/send_reply", methods=["POST"])
def send_reply():
    data = request.json
    subject = data.get("subject")
    reply_text = data.get("reply_text")
    to_email = data.get("to_email", "shwetaumbrajkaar11@gmail.com")
    email_id = data.get("email_id")
    result = send_reply_email(subject, reply_text, to_email, email_id)
    if result == "Replied" and email_id is not None:
        global emails
        emails[email_id]["status"] = "replied"
    return {"status": result}

@app.route("/email_management", methods=["GET", "POST"])
def email_management():
    emails = fetch_and_analyze_emails()
    filter_sentiment = request.form.get("filter_sentiment", "all")
    filter_status = request.form.get("filter_status", "all")
    if filter_sentiment != "all":
        emails = [email for email in emails if email["sentiment"] == filter_sentiment.upper()]
    if filter_status != "all":
        emails = [email for email in emails if email["status"] == filter_status.lower()]
    
    sentiment_counts = {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0}
    for email in fetch_and_analyze_emails():
        sentiment_counts[email["sentiment"]] += 1
    
    return render_template("email_management.html", emails=emails, filter_sentiment=filter_sentiment, filter_status=filter_status, sentiment_counts=sentiment_counts)

@app.route("/email_detail/<int:index>")
def email_detail(index):
    emails = fetch_and_analyze_emails()
    if 0 <= index < len(emails):
        email = emails[index]
        return render_template("email_detail.html", email=email)
    return "Email not found", 404

if __name__ == "__main__":
    app.run(debug=True)