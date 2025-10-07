#! /usr/bin/env python3
"""
botograder_canvas.py 
Pulls student notebooks from assignments in Canvas LMS.  
Then submits scores as grades for assignments -- Assumes 10 points? 
Requires text file "CANVAS_API_KEY.txt" in the current directory when executed.
"""

import argparse 
from canvasapi import Canvas, exceptions

from botograder.core import run_nb, get_tests_passed
from botograder.canvas_utils import get_api_key, parse_assignment_url, is_new_submission
from botograder.utils import string_to_file


# global variables to be overwritten later
drive = None 
id_to = None
API_URL = None
API_KEY = None


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
    # note Test student id changes with each assignment. 
    id_to = {}
    id_to[37851] = {"name":"Test_Student", "email":"nobody@nobody.org"} # it was this for assn 5
    for user in users:
        #print("user = ",user)
        id_to[user.id]= {"name":user.name.replace(' ','_'), "email":user.email}

    # Download all the submitted files
    #download_submissions(assignment, dst_dir=assignment_dir)

    ## Download and run students' notebooks
    subs = assignment.get_submissions() 
    i, nfiles = 0,0
    for s in subs:
        if s.user_id not in id_to.keys(): 
            print(f"\nUser id {s.user_id} not found in id_to dict. Adding as Probably_Test_Student")
            id_to[s.user_id] = {"name":"Probably_Test_Student", "email":"nobody@nobody.org"} 
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
                #total_tests = run_log.count('Running test')
                #tests_passed = run_log.count('Test passed!')
                tests_passed, total_tests = get_tests_passed("run_log.txt")
                score = 0
                if tests_passed > 0:
                    percent = (tests_passed*1.0 / total_tests) 
                    score = percent * assignment.points_possible
                    print(f"Score = {score}. = {tests_passed}/{total_tests} * ({assignment.points_possible} points possible)")
                else: 
                    print("No tests passed. Score = 0")
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