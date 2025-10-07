import os
import re
import datetime
from botograder.core import get_tests_passed

API_KEY = None 
def get_api_key(
    keyfile = "CANVAS_API_KEY.txt" # a text file where the only line is your Canvas API key
    ):
    global API_KEY 
    API_KEY = None
    try:
        with open(keyfile, "r") as f:
            API_KEY = f.readline().strip()
    except: 
        print(f"Error trying to load API Key from file {keyfile}")
    return API_KEY



def parse_assignment_url(url):
    # I used ChatGPT to generate this code
    # Define a regular expression pattern to match numbers in the URL
    pattern = r'\d+'
    
    # Use re.findall to find all matching numbers in the URL
    numbers = re.findall(pattern, url)
    
    # Check if we have at least two numbers
    if len(numbers) >= 2:
        # Convert the first two numbers to integers
        course_id = int(numbers[0])
        assn_id = int(numbers[1])
        
        # Return a tuple of the two numbers
        return (course_id, assn_id)
    else:
        # Return None if there are not enough numbers in the URL
        return None    
    return course_id, assn_id



def is_new_submission(submission, local_filename):
    if not os.path.exists(local_filename):
        print("No local file found. Downloading submission.")
        return True
    subdatetime = datetime.datetime.strptime(submission.submitted_at, '%Y-%m-%dT%H:%M:%SZ')
    subdatetime = subdatetime - datetime.timedelta(hours=6) # Canvas operates in European Central time, so we need to subtract for US Central time
    filetimestamp = os.path.getmtime(local_filename)
    filedatetime = datetime.datetime.fromtimestamp(filetimestamp)
    result = subdatetime > filedatetime
    print(f"subdatetime = {subdatetime}, filedatetime = {filedatetime}, is_new_submission = {result}")
    return result
