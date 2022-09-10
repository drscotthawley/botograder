# botograder
An autograder. There are many like it but this one is mine


Downloads and runs parts of Google Colab notebooks when they change.

## Requirements:
```bash
pip install pydrive2 jupytext
```

## Requried Files: 
```
   imports.py     = where teacher's imports are specified (students aren't allowed to import)
   tests.py       = where teacher's tests are written -- these call the students' subroutines
   valid_emails.txt  = comma-separated list of email addresses of all students in class. 
   settings.yaml = contains google drive oauth2 client app id & authentication secret
        Sample settings.yaml file: 
        https://github.com/iterative/PyDrive2/blob/main/examples/Upload-and-autoconvert-to-Google-Drive-Format-Example/settings.yaml
```

## Instructions:
1. Make yourself an authenticated Google Drive API app: First set up Google credentials for PyDrive2 usage: cf. https://docs.iterative.ai/PyDrive2/quickstart/ -- **this is nontrivial and the bulk of the work is getting everything correct**. 

2. Replace the `settings.yaml` and `credentials.json` files with your own, as per PyDrive2 Quckstart doc.   Run the `python quickstart.py` provided in the PyDrive2 doc. 

3. Set up the assignment: Create a directory like `examples/assignment_2/`. Therein place your `imports.py` and `tests.py` for that assignment. Student code in the form of classes and functions ("`def`") will get sandwiched between those files you provide. 

4. Limit who's in your course (to avoid spam/spamming): Replace `valid_emails` with a list of your own students' emails.

5. Create a Google Form for the Assignment whereby students can provide their names, emails, and "sharing links" to their Colab notebooks.   Sample form: https://forms.gle/udBpUpHifdAwLmU96


6. Generate a Google Sheet from that form, and supply the sharing URL to *that* (e.g. https://docs.google.com/spreadsheets/d/16S5jfbbVWj3Os2MQNe0oTH08f7u8pLEduto9x0BtNc4/edit?usp=sharing) into botograder

## Sample Usage:

```bash
./botograder.py -n examples/assignment2 https://docs.google.com/spreadsheets/d/16S5jfbbVWj3Os2MQNe0oTH08f7u8pLEduto9x0BtNc4/edit?usp=sharing
```


