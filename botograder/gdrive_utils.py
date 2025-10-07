
from dateutil.parser import parse as parsedate


def url_to_id(url, split_ind=4):
    "convert google drive file urls to file ids"
    if 'spreadsheets' in url: split_ind = 5
    id =  url.split('/')[split_ind]
    id = id.replace('?usp=sharing','')
    return id

def ss_sharing_url_to_csv(url):
    "convert spreadsheet sharing url to csv url"
    return url.replace('edit?usp=sharing','gviz/tq?tqx=out:csv&sheet=Sheet1')

def gdrive_file_date(url):
    "get data for a file stored on gdrive"
    id = url_to_id(url)
    gd_file = drive.CreateFile({'id': id})
    gd_file['modifiedDate']
    return parsedate(gd_file['modifiedDate']).astimezone()

