# botograder
An autograder. There are many like it but this one is mine


Downloads and runs parts of Google Colab notebooks when they change.

## Requirements:
```bash
pip install pydrive2 jupytext
```

## Instructions:
First setup Google credentials for PyDrive2 usage: cf. https://docs.iterative.ai/PyDrive2/quickstart/ -- **this is nontrivial and the bulk of the work is getting everything correct**. 

Create a directory like assignment_2/ and in there place imports.py and test.py for that assignment...

## Requried Files: 
   imports.py     = where teacher's imports are specified (students aren't allowed to import)
   tests.py       = where teacher's tests are written -- these call the students' subroutines
   valid_emails.txt  = comma-separated list of email addresses of all students in class. 
   settings.yaml = contains google drive oauth2 client app id & authentication secret
                   See pydrive2 docs: https://github.com/iterative/PyDrive2
                   Setting up a Google Drive App is nontrivial BTW ;-)

Sample settings.yaml file: 
  https://github.com/iterative/PyDrive2/blob/main/examples/Upload-and-autoconvert-to-Google-Drive-Format-Example/settings.yaml


