Sentiment Watchdog

Welcome to Sentiment Watchdog, a powerful tool for analyzing customer emotions from text, speech, or chat data. This project leverages AI to provide real-time insights and actionable suggestions, helping businesses enhance customer experience.

Overview
Sentiment Watchdog processes customer feedback, emails, and tickets to detect emotions (e.g., joy, anger, sadness) and sentiments (positive, negative, neutral). It includes a user-friendly interface with dashboards, email management, and AI-driven response generation.

Features
Real-Time Emotion Analysis: Uses the j-hartmann/emotion-english-distilroberta-base model to classify emotions.
Email Fetching: Fetches emails from Gmail via IMAP, analyzing content on the fly.
AI Suggestion Button: Generates tailored reply suggestions based on email emotions (e.g., apologetic responses for anger).
Dashboard: Visualizes sentiment trends, department performance, and word clouds.
CSV Upload: Import customer data for analysis.
Email Management: View, filter, and reply to emails with status tracking.
Chatbot: Provides basic support and guidance.

Recent Updates
Added email fetching functionality with JSON payload fixes to resolve 415 errors.
Implemented an AI suggestion button for generating responses, overcoming visibility bugs.
Enhanced UI with two new centered emojis below the original four, maintaining animations.
Ensured status updates for emailed replies using global email list management.

Prerequisites
Python 3.8+
Conda (optional for environment management)
Required Python libraries (install via requirements.txt):
flask
pandas
transformers
slack_sdk
wordcloud
imaplib
smtplib

Setup Instructions
1) Clone the Repository:
  git clone https://github.com/ShwetaUmbrajkar/Sentiment-Watchdog.git
  cd Sentiment-Watchdog

2) Set Up Environment:
Create a Conda environment (optional):
  conda create -n sentiment_env python=3.8
  conda activate sentiment_env

Install dependencies:
  pip install -r requirements.txt

3) Configure Secrets:
Update app.py with your Gmail credentials (lines ~20-25) and Slack token (line ~33) or use environment variables (e.g., .env file with python-dotenv).
  EMAIL_USER=your.email@gmail.com
  EMAIL_PASS=your_app_password
  SLACK_TOKEN=xoxb-your-slack-token

Add .env to .gitignore.

4) Run the Application:
  python app.py
Access at http://127.0.0.1:5000/.

Usage
Upload CSV: Use the "Upload CSV Report" flashcard to analyze ticket data.
Fetch Emails: Click "Fetch Emails" on the Upload page to retrieve and analyze the latest email.
Generate AI Suggestion: Click the button to get a tailored reply, then send it.
Dashboard: View insights and trends.

Contributing
Feel free to fork this repository, submit issues, or pull requests. Suggestions for optimizing AI responses or UI enhancements are welcome!

License
MIT License - Feel free to modify and distribute.

Contact
Author: Shweta Umbrajkar
Email: shwetaumbrajkaar11@gmail.com
