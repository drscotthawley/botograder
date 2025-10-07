#! /usr/bin/env python3
"""
botograder_local.py 
Runs locally expecting all students work is in files on the current system
Doesn't email anybody
"""

import datetime
#from tkinter import TRUE
import requests
from dateutil.parser import parse as parsedate
import os, sys
import pandas as pd
import time
import subprocess
import smtplib
from email.message import EmailMessage
import yagmail
import glob
import re
import argparse 

# global variables to be overwritten:
drive = None 

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


def download_if_newer_generic(url, dst_file, force_new=False, date_key='Date'):
    """
    For generic, ordinary files
    cf. https://stackoverflow.com/questions/29314287/python-requests-download-only-if-newer
    """
    r = requests.head(url)
    url_date = parsedate(r.headers[date_key]).astimezone()
    if not os.path.exists(dst_file):
        force_new = True
    else:
        file_date = datetime.datetime.fromtimestamp(os.path.getmtime(dst_file)).astimezone()
    print("url_date = ",url_date)
    print("file_date = ",file_date)
    if (force_new) or (url_date > file_date):
        print(f"Downloading {dst_file} from {url}...")
        user_agent = {"User-agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:46.0) Gecko/20100101 Firefox/46.0"}
        r = requests.get(url, headers=user_agent)
        with open(dst_file, 'wb') as fd:
            for chunk in r.iter_content(4096):
                fd.write(chunk)


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


def download_if_newer_gdrive(url, dst_file, force_download=False, date_key='modifiedDate', colab=False):
    """
    downloads a file from url if it's newer than dst_file stored on local disk. 
    """
    updated = False

    url_date = gdrive_file_date(url)

    if not os.path.exists(dst_file):
        force_download = True
    else:
        file_date = datetime.datetime.fromtimestamp(os.path.getmtime(dst_file)).astimezone()

    if (force_download) or (url_date > file_date):
        print(f"Downloading new version of {dst_file}")
        wget_useragent_str = 'wget -q -U "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)"'
        if colab:
            ### "wget -q -U "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)" -O examples/assignment_2/B00000000_Scott_Hawley.ipynb  'https://docs.google.com/uc?export=download&id=16-zOEoHEtLO8k_Nm8YytHIGsTdao2yrz'"
            url = f"'https://docs.google.com/uc?export=download&id={url_to_id(url)}'"
        cmd = f"rm -f {dst_file}; {wget_useragent_str} -O {dst_file} {url}"
        print("\ncmd = ",cmd)
        run_cmd(cmd)
        updated = True
    else:
        pass #print(f"We already have the latest version of {dst_file}.")

    return updated


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

    file1 = open(pyfile, 'r')
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
    cmd = f'jupytext --to py {nb_file}'
    print(f"Converting notebook: {nb_file}\n  {cmd}")
    run_cmd(cmd)                # convert notebook to python script
    pyfile = nb_file.replace('ipynb','py')
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


if __name__=="__main__":

    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('dir', default="assignment_N", help='directory to execute nbs in')
    args = p.parse_args()
    assignment_dir = args.dir

    ## Update & run students' Colab notebooks
    names = ['shawley',]# ***HERE*** add student usernames as in /home directory
    for name in names:
        print(f"\n\n=================== Beginning Run for Name: {name} ==================== ")
        orig_file = f'/home/{name}/DLAIE/Assignments/A5_GANs.ipynb'
        dst_file = f'{assignment_dir}/{name}_A5_GANs.ipynb'
        cmd = f"sudo cp {orig_file} {dst_file}; sudo chown mchorse {dst_file}"
        os.system(cmd)
        run_log = run_nb(dst_file, assignment_dir=assignment_dir, name=name) # Run the notebook
        print(f"\n\n=================== End of Run for Name: {name} ====================\n ")
