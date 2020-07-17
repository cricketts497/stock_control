from PyQt5.QtCore import QObject
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import datetime as dt
import pandas as pd
import io


class DriveAccess(QObject):
    SCOPES = ['https://www.googleapis.com/auth/drive.file'] # view and manage files created with this app
    CREDENTIALS = "../client_secret.json" # file path to the credentials file
    def __init__(self):
        super().__init__()
        
        #dict to connect the filenames with file_ids
        self.file_ids = {}
        
        #connect with google drive to let the user log in
        flow = InstalledAppFlow.from_client_secrets_file(self.CREDENTIALS, self.SCOPES)
        creds = flow.run_local_server(port=0)
        
        #service to send the requests to
        self.service = build('drive', 'v3', credentials=creds)
        
    def pull(self, filename):
        """
        Pull down the data files 
        
        Arguments:
            filename: Name of the file we want to pull down
        """
        if filename not in self.file_ids.keys():
            results = self.service.files().list(q="name = '{}'".format(filename), pageSize=10, fields="nextPageToken, files(id, name, modifiedTime)").execute()
            items = results.get('files', [])

            if not items:
                print('No files found.')
            else:
                print('Files:')
                files = pd.DataFrame()
                for item in items:
                    print(u'{0}, {1}, {2}'.format(item['name'], item['id'], item['modifiedTime']))
                    files = files.append({'name':item['name'], 'id':item['id'], 'time':item['modifiedTime']}, ignore_index=True)
                
                files.time = pd.to_datetime(files.time, errors='coerce')
                files = files.sort_values('time', ascending=False)
                print(files)
                self.file_ids[filename] = files.id.iloc[0]
                
        print(self.file_ids[filename])
        
        #download the file
        request = self.service.files().get_media(fileId = self.file_ids[filename])
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            print('Download: {} %'.format(status.progress()*100))

        fh.seek(0)
        df = pd.read_csv(fh, encoding='utf-8')

        return df
        
    def push(self, df, filename):
        """
        Push the input dataframe back to drive with the input filename
        
        Arguments:
            df: pd.DataFrame(), the data to upload
            filename: str, the path to save to
        """
        #save the file locally, if this raises a PermissionError then we return with that error
        df.to_csv(filename)
        
        file_metadata = {
        'name': filename
        }
        media = MediaFileUpload(filename,
                                mimetype='text/csv',
                                resumable=True)
        file = self.service.files().create(body=file_metadata,
                                            media_body=media,
                                            fields='id').execute()
        
        self.file_ids[filename] = file.get('id')
        print('{0}, File ID: {1}'.format(filename, self.file_ids[filename]))
        
        
        
            
if __name__ == "__main__":
    da = DriveAccess()
    df = da.pull('orders.csv')
    
    try:
        da.push(df, 'orders.csv')
    except PermissionError:
        print('perm error')
        
    print(da.pull('orders.csv'))
    
        
        
    