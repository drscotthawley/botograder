#! /usr/bin/env python3
"""
botograder_canvas_lb.py 
runs leaderboard from canvas 
"""

import argparse 
from canvasapi import Canvas, exceptions
import sys
import os

from botograder.core import run_nb, get_tests_passed
from botograder.canvas_utils import get_api_key, parse_assignment_url, is_new_submission
from botograder.utils import string_to_file, run_cmd


# global variables to be overwritten later
drive = None 
id_to = None
API_URL = None
API_KEY = None



def do_lb_stuff(nb_filename:str, # notebook file
                lb_dir=".", # place where leaderboard executables and csv's are
                ):
    """run all the leaderboard stuff
    only executes once the notebook has been downloaded"""

    # convert to python
    cmd = f'jupytext --to py {nb_filename}'
    print(f"Converting to Python: {cmd}")
    run_cmd(cmd)
    py_filename = nb_filename.replace('ipynb','py')

    print("Running leaderboard evaluation...")

    # Save current directory and switch to lb_dir
    save_cwd = os.getcwd()
    if lb_dir != save_cwd:
        os.chdir(lb_dir)
    
    try:
        # Get absolute path to submission since we changed dirs
        abs_py_path = os.path.abspath(os.path.join(save_cwd, py_filename))
        
        run_cmd(f"python evaluate_submission.py --submission {abs_py_path}")
        run_cmd(f"python generate_leaderboard.py")
        run_cmd(f"git add leaderboard.csv")
        run_cmd(f"git commit -m 'Update leaderboard with new submission'")
        run_cmd(f"git push")
        
        print("Leaderboard updated successfully!")
        return True
        
    finally:
        # Always restore original directory, even if error occurs
        os.chdir(save_cwd)




if __name__=="__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('-t', '--test', action='store_true', help="Test mode: don't actually submit grades/logs to Canvas")
    p.add_argument('url', help='url pointing to assignment in Canvas')
    p.add_argument('dir',  help='local directory to execute nbs in')
    args = p.parse_args()
    test_mode = args.test
    assn_url = args.url
    assignment_dir = args.dir # local directory 
    os.makedirs(assignment_dir, exist_ok=True)


    # Canvas Setup
    API_URL = "https://belmont.instructure.com"   # Canvas API URL
    API_KEY = get_api_key()
    course_id, assn_id = parse_assignment_url(assn_url)
    canvas = Canvas(API_URL, API_KEY) # create a canvas object
    course = canvas.get_course(course_id)
    assignment = course.get_assignment(assn_id)
    users = list(course.get_users(enrollment_type=['student']))

    ## Download and run students' notebooks
    subs = assignment.get_submissions(include=['user'])
    i, nfiles = 0,0

    for i, s in enumerate(list(subs)):
        user_name = s.user['name']
        print(f"-----\ni={i}: {user_name}")
        
        if not hasattr(s, 'attachments') or len(s.attachments) == 0:
            print("No file submitted")
            continue
        
        # Rest of processing
        thefile = s.attachments[-1]
        
        nb_file = f"u{s.user_id}_{user_name.replace(' ','_')}.ipynb"
        outname = f"{assignment_dir}/{nb_file}"
        
        if is_new_submission(s, outname):
            nfiles += 1
            print(f"Downloading: {outname}")
            thefile.download(outname)
            do_lb_stuff(outname)
        else:
            print(f"Already have latest version")

    print(f"Downloaded {nfiles} files")