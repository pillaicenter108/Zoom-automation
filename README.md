🚀 Setup Instructions
1. Install dependencies
uv pip install -r requirements.txt
2. Install project (editable mode)
uv pip install -e .
3. Add config folder
Create a folder named config/
Inside it, add:
service_account.json
4. Add environment file
Create a .env file in root directory
Add required environment variables
5. Run the application
python -m streamlit run zoom_automation/api/app.py