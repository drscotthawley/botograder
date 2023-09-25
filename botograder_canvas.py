#! /usr/bin/env python3
"""
botograder_canvas.py 
Pulls student notebooks from assignments in Canvas LMS.  
Then submits scores as grades for assignments -- Assumes 10 points? 
Requires text file "CANVAS_API_KEY.txt" in the current directory when executed.
"""

import datetime
#from tkinter import N
#from tkinter import TRUE
import requests
from dateutil.parser import parse as parsedate
import os, sys
import pandas as pd
import time
import subprocess
import glob
import re
import argparse 
from canvasapi import Canvas, exceptions
import datetime

# global variables to be overwritten later
drive = None 
API_KEY = None
API_URL = None
id_to = None

def get_api_key(
    keyfile = "CANVAS_API_KEY.txt" # a text file where the only line is your Canvas API key
    ):
    API_KEY = None
    try:
        with open(keyfile, "r") as f:
            API_KEY = f.readline().strip()
    except: 
        print(f"Error trying to load API Key from file {keyfile}")
    return API_KEY


def string_from_file(filename="txt_file.txt"):
    "just read a string from a text file"
    output = ''
    try: 
        text_file = open(filename, "r")
        output = text_file.read().strip()
        text_file.close()
    except: 
        print(f"Error: cannot read file {filename}")
    return output

def string_to_file(s, filename="txt_file.txt"):
    text_file = open(filename, "w")
    n = text_file.write(s)
    text_file.close()

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

def wait_til_file_ready(dst_file, sleep=1):
    "sometimes it takes a little while for a local file to be created from (gdrive) download"
    while not os.path.exists(dst_file):
        print(f"Waiting til file {dst_file} is ready")
        time.sleep(sleep)


def run_cmd(cmd, log=False, restricted=True):
    "wrapper for running a unix shell command"
    # TODO: trap for possible problems when in restricted mode
    if log: print("    cmd = ",cmd)
    #os.system(cmd)
    return subprocess.getoutput(cmd)


def skip_this_line(line, allow_imports=False):
    """
    Many lines in the notebook py file need not be copied to local version that will be executed
    Even allowing student imports could be risky, e.g.
        import os as o
        o.system('rm -f *')
    """
    skip = False
    if (line == '') or (line == '\n'): skip = True    # skip blank lines
    prohibited = ['subprocess','fork','exec', 'popen','shutil',' os.c',' os.d',
        ' os.f',' os.g',' os.m',' os.pu',' os.r',' os.s',' os.u',
        'credentials.json','id_rsa']  # risky stuff, will not be executed from student's notebook
    if any(s in line for s in prohibited): skip = True
    if (not allow_imports) and any(s in line for s in ['import ']): skip = True
    return skip


def grab_top_lev(pyfile, dir, debug=False, stop_after='token_to_one_hot', imports_wherever=True):
    """
    Student exercises will only occur inside functions and classes
    Grab relevant imports, function defs, or class defs
    Ignore any other text --  esp. as it might generate syntax / IndentationError we don't care about
    """
    out_text = ''
    rec_start_cue = ' GRADED EXERCISE'  # leading space is there to differentiate from "UNGRADED EXERCISE"
    block_name_cues = ['def','class']  # these all have to start in column 1
    also_allowed = ['nltk.']  # these all have to start in column 1
    print(f"  Trying to open file {dir+'/'+pyfile}")
    file1 = open(dir+'/'+pyfile, 'r')
    lines = file1.readlines()
    recording, already_found_stop = False, False
    block_started, block_name = False, ''    # block is a function or class
    for i, line in enumerate(lines):
        if skip_this_line(line): continue
        line = line.replace('\t','    ')  # convert tabs to spaces
        first_char, first_nonws_char, first_word = line[0], line.replace(' ','')[0], line.split(' ')[0]  # first things
        if first_nonws_char in ['!','%']: continue   # skip jupyter magics like !pip, %matplotlib

        if imports_wherever and (first_word in also_allowed):
            out_text += line
            continue

        # skip lines unindented comments except for the rec_start_cue
        if (first_char == '#') and (rec_start_cue not in line): continue

        if rec_start_cue in line:
            recording = True
            if debug: print(f"line = {line}. RECORDING = {recording}")
            out_text += '\n\n'   # cosmetic but nice
        elif recording:
            if (not imports_wherever) and (first_word in also_allowed):
                out_text += line
                continue
            if (not block_started) and (first_word in block_name_cues):
                block_started = True
                block_name = line.split(' ')[1].split('(')[0]
                print(f'    started block {block_name}')
            elif ((block_started) and (first_word in block_name_cues)) or (first_word != ''):
                block_started = False
                recording = False
                if debug: print(f"line = {line}. RECORDING = {recording}")
                if (block_name == stop_after):
                    if debug: print(f"line = {line}, reached end of stop_after={stop_after}.  Returning")
                    return out_text
        if recording: out_text += line
    return out_text


def clean_user_str(s:str):
    """Security: s is a user input that we'll end up using to name files and run shell commands,
    so we need to 'clean' it to guard against injection attacks / arbitrary code execution"""
    disallowed_chars = [';','|','>','<','*']  # Google urls will use ?, &, / : a-zA-Z0-9, = btw
    escaped_chars = []
    for c in disallowed_chars: s = s.replace(c,'')   # remove
    for c in escaped_chars: s = s.replace(c,'\\'+c)   # escape via backslash
    return s

def remove_syntax_errors(py_file):
    cmd = f"python -m py_compile {py_file}"  # 2>&1 >/dev/null |  grep ', line '"
    precheck_str = run_cmd(cmd)
    if precheck_str != '':
        print("Syntax pre-check problem: ",precheck_str)
        bad_lines = re.findall(f", line \d+",precheck_str)
        if len(bad_lines) > 0:
            bad_line = int(bad_lines[0].split(' ')[-1])
            print("Removing bad line",bad_line)
            lines = []
            with open(py_file, 'r') as fp: # read file into list
                lines = fp.readlines()
            del lines[bad_line-1]          # remove bad line
            with open(py_file, 'w') as fp: # overwrite file without bad line. 
                fp.writelines(lines)
            remove_syntax_errors(py_file) # recursion!
        else:
            print("\n\n******ERROR: Don't know how to fix this*****\n\n")


def run_nb(nb_file, funcs=['count_freqs'], assignment_dir="./", student_id='', name=''): 
    """
    Run (parts of) the student's notebook using imports & tests supplied by teacher
    """
    path = f"{assignment_dir}/{nb_file}".replace(' ','\ ').replace('(','\(').replace(')','\)')
    cmd = f'jupytext --to py {path}'
    print(f"Converting notebook: {nb_file}\n  {cmd}")
    run_cmd(cmd)                # convert notebook to python script
    pyfile = nb_file.replace('.ipynb','.py')
    student_parts = f'{assignment_dir}/student_parts.py'  # where we'll save the grabbed parts of the student's file
    nb_py_text = grab_top_lev(pyfile, assignment_dir)     # grab the relevant parts of the student's code
    with open(student_parts, 'w') as f:
        f.write(nb_py_text)                                # write that to a text file called student_parts

    imports = f'{assignment_dir}/imports.py'                  # where teacher's predefined imports lie
    tests = f'{assignment_dir}/tests.py'                      # where teacher's tests are written
    tester_file = f"{assignment_dir}/{student_id}_{name.replace(' ','_')}_run_assignment.py"      # the complete file that we'll be running
    run_cmd(f"cat {imports} {student_parts} {tests} > {tester_file}")  # assemble the run file
    remove_syntax_errors(tester_file)
    print(f">>> Executing testing file: {tester_file}")
    run_log = run_cmd(f"python {tester_file}")
    run_log = f"Run log for {nb_file}:\n" + run_log
    if 'tests passed.' not in run_log[-20:]: run_log += "\n\n0 tests passed." # if the whole thing crashed
    print(run_log)
    return run_log


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
    filetimestamp = os.path.getmtime(local_filename)
    filedatetime = datetime.datetime.fromtimestamp(filetimestamp)
    result = subdatetime > filedatetime
    print(f"subdatetime = {subdatetime}, filedatetime = {filedatetime}, is_new_submission = {result}")
    return result



if __name__=="__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('-t', '--test', action='store_true', help="Test mode: don't actually submit grades/logs to Canvas")
    p.add_argument('url', help='url pointing to assignment in Canvas')
    p.add_argument('dir',  help='local directory to execute nbs in')
    args = p.parse_args()
    test_mode = args.test
    assn_url = args.url
    assignment_dir = args.dir # local directory 

    # Canvas Setup
    API_URL = "https://belmont.instructure.com"   # Canvas API URL
    API_KEY = get_api_key()

    #course_id =  15626 # DLAIE, Fall 23
    #assn_url = 'https://belmont.instructure.com/courses/15626/assignments/284175' # Assignment 2, Fall2023
    #assn_url = 'https://belmont.instructure.com/courses/15626/assignments/307639' # Assignment 3, Fall2023

    course_id, assn_id = parse_assignment_url(assn_url)

    canvas = Canvas(API_URL, API_KEY) # create a canvas object
    course = canvas.get_course(course_id)
    assignment = course.get_assignment(assn_id)
    users = course.get_users(enrollment_type=['student'])
    id_to = {36533: {"name":"Test_Student", "email":"nobody@nobody.org"}}
    for user in users:
        id_to[user.id]= {"name":user.name.replace(' ','_'), "email":user.email}

    # Download all the submitted files
    #download_submissions(assignment, dst_dir=assignment_dir)

    ## Download and run students' notebooks
    subs = assignment.get_submissions() 
    i, nfiles = 0,0
    for s in subs:
        #print(s.__dir__())
        print(f"-----\ni={i}: {id_to[s.user_id]['name']}                   {id_to[s.user_id]['email']} ")
        if len(s.attachments) > 0:
            nfiles +=1 
            #print(s.__dir__())
            thefile = s.attachments[-1]
            thefile_name = f"{thefile}".replace(' ','').replace('(','').replace(')','') # strip bad chars
            print(f"File uploaded is {thefile}")
            nb_file = f"a{s.assignment_id}_u{s.user_id}_{id_to[s.user_id]['name']}_{thefile_name}"
            nb_file = nb_file.replace("'","").replace("/","").replace(";","").replace("&","") # strip bad chars
            outname = assignment_dir+'/'+nb_file
            if is_new_submission(s, outname):
                print(f"Saving new submission to {outname}")
                thefile.download(outname)
                # Run the notebook

                #if 'Test' not in nb_file: continue  # Only run for Test Student

                print(f"\n\n=================== Beginning Run for File: {nb_file} ==================== ")
                run_log = run_nb(nb_file, assignment_dir=assignment_dir, name=id_to[s.user_id]['name']) 

                print(f"\n\n=================== End of Run for Name: {nb_file} ==================== ")
                string_to_file(run_log, "run_log.txt")

                # create a score
                total_tests = run_log.count('Running test')
                tests_passed = run_log.count('Test passed!')
                score = 0
                if tests_passed > 0:
                    percent = (tests_passed*1.0 / total_tests) 
                    score = percent * assignment.points_possible
                print("Score = ",score)
                if not test_mode:
                    print("Submitting grades and run log")
                    s.edit(submission={'posted_grade':score})
                    s.upload_comment("run_log.txt")
                    print("Finished submitting grade.\n\n")
                else:
                    print("Test mode: No grade submitted")
            else:
                print(f"Submission not updated. Filename was {outname}")
        else:
            print("Nothing submitted yet.")
        i += 1
    lsubs = i

    print(f"All graded. Canvas says {lsubs} submissions (including empty submissions). Only {nfiles} files were downloaded and graded.")