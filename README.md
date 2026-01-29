# AI Money Friends 💰

AI-powered financial education platform for kids.

## Features

- **Social Login**: Support for Kakao, Naver, and Google OAuth login
- **AI Chatbot**: Interactive financial education chatbot powered by Google Gemini
- **Financial Education**: Age-appropriate financial lessons and activities
- **Parent Dashboard**: Monitor your child's financial learning progress
- **Child Dashboard**: Fun and engaging interface for kids to learn about money

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd "JB AI Money Kids"
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root:
```env
# Social Login
KAKAO_CLIENT_ID=your_kakao_client_id
KAKAO_REDIRECT_URI=http://localhost:8501

NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret
NAVER_REDIRECT_URI=http://localhost:8501

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8501

# AI API Keys
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
```

## Running the Application

Start the Streamlit app:
```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`

## Environment Variables

### Social Login

- `KAKAO_CLIENT_ID`: Kakao REST API Key
- `KAKAO_REDIRECT_URI`: Redirect URI for Kakao OAuth
- `NAVER_CLIENT_ID`: Naver Client ID
- `NAVER_CLIENT_SECRET`: Naver Client Secret
- `NAVER_REDIRECT_URI`: Redirect URI for Naver OAuth
- `GOOGLE_CLIENT_ID`: Google Client ID
- `GOOGLE_CLIENT_SECRET`: Google Client Secret
- `GOOGLE_REDIRECT_URI`: Redirect URI for Google OAuth

### AI Services

- `GEMINI_API_KEY`: Google Gemini API key
- `GROQ_API_KEY`: Groq API key (optional)

## Deployment (Streamlit Cloud)

1. Push your code to GitHub
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Create a new app and connect your repository
4. Add secrets in the app settings:

```
[oauth]
kakao_client_id = "your_kakao_client_id"
kakao_redirect_uri = "https://your-app.streamlit.app"
naver_client_id = "your_naver_client_id"
naver_client_secret = "your_naver_client_secret"
naver_redirect_uri = "https://your-app.streamlit.app"
google_client_id = "your_google_client_id"
google_client_secret = "your_google_client_secret"
google_redirect_uri = "https://your-app.streamlit.app"
```

## Project Structure

```
.
├── app.py                 # Main application file
├── services/
│   ├── oauth_service.py   # OAuth service (Kakao, Naver, Google)
│   ├── gemini_service.py  # Google Gemini AI service
│   └── conversation_service.py  # Chat conversation service
├── database/
│   └── db_manager.py      # Database management
├── utils/
│   ├── menu.py            # Sidebar menu
│   └── auth.py            # Authentication utilities
├── pages/                 # Streamlit pages
│   ├── 1_💬_아이_채팅.py
│   ├── 7_🎯_금융_미션.py
│   └── 8_📖_금융_스토리.py
├── .env                   # Environment variables (local)
├── .env.example           # Environment variables template
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on GitHub.
