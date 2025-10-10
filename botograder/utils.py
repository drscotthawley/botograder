import subprocess
import time
import os 



def string_to_file(s, filename="txt_file.txt"):
    text_file = open(filename, "w")
    n = text_file.write(s)
    text_file.close()



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


def clean_user_str(s:str):
    """Security: s is a user input that we'll end up using to name files and run shell commands,
    so we need to 'clean' it to guard against injection attacks / arbitrary code execution"""
    disallowed_chars = [';','|','>','<','*']  # Google urls will use ?, &, / : a-zA-Z0-9, = btw
    escaped_chars = []
    for c in disallowed_chars: s = s.replace(c,'')   # remove
    for c in escaped_chars: s = s.replace(c,'\\'+c)   # escape via backslash
    return s


def run_cmd(cmd, log=False, restricted=True, stream=True, timeout=None):
    "wrapper for running a unix shell command"
    if log: print("    cmd = ",cmd)
    
    if stream:
        import subprocess
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, 
                                   stderr=subprocess.STDOUT, text=True)
        output = []
        try:
            for line in process.stdout:
                print(line, end='')
                output.append(line)
            process.wait(timeout=timeout)
            return ''.join(output)
        except subprocess.TimeoutExpired:
            process.kill()
            output.append(f"\n❌ Process timed out after {timeout} seconds\n")
            return ''.join(output)
    else:
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, 
                                  text=True, timeout=timeout)
            return result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return f"❌ Process timed out after {timeout} seconds"
           

def wait_til_file_ready(dst_file, sleep=1):
    "sometimes it takes a little while for a local file to be created from (gdrive) download"
    while not os.path.exists(dst_file):
        print(f"Waiting til file {dst_file} is ready")
        time.sleep(sleep)

