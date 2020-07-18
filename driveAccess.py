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
        self.file_mod_times = {}
        
        #connect with google drive to let the user log in
        flow = InstalledAppFlow.from_client_secrets_file(self.CREDENTIALS, self.SCOPES)
        creds = flow.run_local_server(port=0)
        
        #service to send the requests to
        self.service = build('drive', 'v3', credentials=creds)
        
    def pull_fileGroup(self, files):
        """
        Pull down multiple files at once
        
        Arguments:
            files: list of filenames
        
        returns:
            list of pd.DataFrames
        """
        frames = []
        for filename in files:
            frames.append(self.pull(filename))
        
        return frames
    
    def push_fileGroup(self, files):
        """
        Push up multiple files at once
        
        Arguments:
            files: list of filenames
        """
        for filename in files:
            self.push(filename)
        
    def getID(self, filename):
        """
        Get the file id for the drive file with the given filename
        
        Arguments:
            filename: str, name of the file
        """
        results = self.service.files().list(q="name = '{}'".format(filename), pageSize=10, fields="nextPageToken, files(id, name, modifiedTime)").execute()
        items = results.get('files', [])

        if not items:
            return False
        else:
            # print('Files:')
            files = pd.DataFrame()
            for item in items:
                # print(u'{0}, {1}, {2}'.format(item['name'], item['id'], item['modifiedTime']))
                files = files.append({'name':item['name'], 'id':item['id'], 'time':item['modifiedTime']}, ignore_index=True)
            
            #get the latest version
            files.time = pd.to_datetime(files.time, errors='coerce')
            files = files.sort_values('time', ascending=False)
            
            self.file_ids[filename] = files.id.iloc[0]
            self.file_mod_times[filename] = files.time.iloc[0]
            
            return True
            
    
        
    def pull(self, filename):
        """
        Pull down the data files 
        
        Arguments:
            filename: Name of the file we want to pull down
        """
        if filename not in self.file_ids.keys():
            success = self.getID(filename)
            if not success:
                raise FileNotFoundError('File not found in google drive')
            
        #download the file
        request = self.service.files().get_media(fileId = self.file_ids[filename])
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            print('Pulling {0}, Download: {1} %'.format(filename, status.progress()*100))

        fh.seek(0)
        df = pd.read_csv(fh, encoding='utf-8')

        return df
        
    def push(self, filename, new=False):
        """
        Push the input dataframe back to drive with the input filename
        
        Arguments:
            filename: str, the path to save to and get the data from
            new: bool, is this a new file upload
        """
        if filename not in self.file_ids.keys() and not new:
            success = self.getID(filename)
            if not success:
                raise FileNotFoundError('File not found in google drive')
        
        file_metadata = {
        'name': filename
        }
        media = MediaFileUpload(filename,
                                mimetype='text/csv',
                                resumable=True)
        
        if new:
            file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            self.file_ids[filename] = file.get('id')
        else:
            file = self.service.files().update(fileId=self.file_ids[filename], body=file_metadata, media_body=media).execute()
        
        print('Pushed {}'.format(filename))
        
            
# if __name__ == "__main__":
    # da = DriveAccess()
    # da.push('stock_adding.csv')
    # df = da.pull('stock_adding.csv')
    # print(df)

    
        
        
    