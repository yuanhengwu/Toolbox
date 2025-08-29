# Toolbox
Collect some tools and routine functions which could be reusable


## Tabs.py
A simple GUI tool to manage URL groups
- Usage:
    - Prepare a JSON file like this:
      ```json
      {
        "AI Tools": [
          "https://chatgpt.com/",
          "https://gemini.google.com/app?hl=zh-TW",
          "https://www.perplexity.ai/"
        ]
      }
      ```
    - Run Tabs.py and Select sessions file
- Note:
    - Verified only on Windows OS for now
    - This version assumes default Chrome and Notepad++ paths:
      ```python
      chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
      notepadpp_candidates = [
          r"C:\Program Files\Notepad++\notepad++.exe",
          r"C:\Program Files (x86)\Notepad++\notepad++.exe"
      ]
      ```
    - You may need to modify them according to your system configuration.


## test.py
A simple script to verify Python environment
- Usage for example:
    - Open Command Prompt and natigate to the script folder
    - Run `python test.py a b c`
    - The output will tell the python version in path, and whether the arguments are passed correctly
- Usage for example:
    - Open Command Prompt and natigate to the script folder
    - Run `test.py a b c`
    - The output will tell the python version according to file association, and whether the arguments are passed correctly
