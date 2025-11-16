from google.oauth2 import service_account
from googleapiclient.discovery import build

# إعدادات Google Drive
SERVICE_ACCOUNT_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# إعداد الاتصال
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=creds)

def list_folders(parent_id):
    """
    ترجع قائمة المجلدات (المواد مثلاً) داخل فولدر السنة الدراسية
    """
    query = f"'{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    return results.get('files', [])

def list_files(folder_id):
    """
    ترجع قائمة الملفات (مثل الباب الأول.pdf) داخل مجلد مادة
    """
    query = f"'{folder_id}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed = false"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])
    
    # نبني روابط مباشرة لكل ملف
    file_links = []
    for file in files:
        link = f"https://drive.google.com/file/d/{file['id']}/view"
        file_links.append((file['name'], link))
    
    return file_links
