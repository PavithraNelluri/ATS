# JobNexus
### Project Overview
This project is designed to help individuals upskill and enhance their career prospects by analyzing their resumes and providing actionable insights and improvement tips. Leveraging AI-driven recommendation systems, the platform suggests personalized courses to bridge skill gaps identified in the resume.

Additionally, the platform acts as a bridge between job seekers and recruiters. With the jobseeker’s consent, it securely shares relevant resume data and key details with recruiters, thereby increasing the chances of job placement.
## Table of Contents
- [Key Features](#key-features)
- [Technologies Used](#technologies-used)
- [Installation](#installation)
- [Run the Project](#run-the-project)
- [Limitations](#limitations)
- [Contributors](#contributors)
---
## Key Features
-  **Resume Analysis**: Evaluates Resume and Provide Resume Score, Missing Skills.
-  **AI-Powered Course Recommendations**: Suggest relevant upskilling courses based on the Missing Skills.
-  **JobSeeker-Recruiter Connection**: Share resumes and essential data with recruiters (only after JobSeeker's consent).
-  **Data Privacy First**: No data is shared without explicit permission from the job seeker.
-  **History Tracking** – Both job seekers and recruiters can view their past activity and interactions.
## Technologies Used
-  **HTML, CSS, JavaScript**: For building a clean and user-friendly frontend interface.
-  **Flask**: Backend framework used to handle server-side logic and routing.
-  **GenAI**: Used for resume and job description parsing, and for Providing smart, AI-driven recommendations.
-  **MySQL**: Used to store and Retrieve important Information.
## Installation
#### 1.Clone the Repository
```bash
git@github.com:PavithraNelluri/ATS.git
```
#### 2.Set Up the DataBase
-  ##### Create a MySQL account if you don’t have one. 
- #####  Log in to MySQL and create a new database and paste the code given in the JobNexus.sql file.
- #####  Create a .env file in your project directory and add the following:

```bash
MYSQL_HOST="your host name"   # usually "localhost"
MYSQL_USER="your user name"  # e.g., "root"
MYSQL_PASSWORD="your password"
MYSQL_DB="your "JobNexus"
```
#### 3.Set Up the GenAI Tools
To enable AI-powered features like resume parsing and smart recommendations, you'll need to get a Groq API key.
- ##### Get Your Groq API Key
  - Go to (https://console.groq.com)
  - Sign up or log in, and generate your API key
- #####  Add the Key to Your .env File
``` bash
GROQ_API_KEY="your groq API key"
```
 Note: Keep your .env file private and never commit it to version control.
#### 4.Create a Virtual Environment
```bash
python -m venv venv
```
#### 5.Activate the virtual environment
- On Windows
```bash
venv/Scripts/activate
```
- On macOS/Linux:
```bash
  source venv/bin/activate
```
#### 6.Install Dependencies
```bash
pip install -r requirements.txt
```
## Run the Project
Once setup is complete, start the application with: 
```bash
python app.py
```
##  Limitations
Occasionally, the Large Language Model (LLM) may take time to respond or fail to return results on the first try.
If that happens, simply refresh the page once or twice to resolve the issue.

We're aware of this problem and will work on improving the stability and reliability in future iterations.


## Contributors
- [PavithraNelluri](https://github.com/PavithraNelluri)
- [Jayanthi-21](https://github.com/Jayanthi-21)


  
