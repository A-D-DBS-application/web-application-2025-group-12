# GroundMatch – Group 12

Intelligent matching system that connects construction companies with ideal building plots that meet their clients' preferences.

![GroundMatch logo](app/static/images/nav/login-page.jpeg)

## How to use the app?

### Introduction
GroundMatch helps construction companies efficiently manage, select, and track suitable building plots for their clients. Thanks to automatic data scraping and an intelligent matching algorithm, your company always has an up-to-date and comprehensive overview of the best plots for each client.

You retain full control: you decide which plots to present to each client, while automatically receiving notifications as soon as new, relevant building plots become available.

Clients see only the top 10 plot matches you select for them and can easily adjust their preferences. This allows you to respond to their needs more quickly and accurately, increase efficiency within your company, and enhance the quality of your service with GroundMatch.

### What you can do as a building company:
- Register and log in to access your company dashboard.
- Manage clients: add clients, view their information, and track their preferences. 
- Manage building plots: add your own plots, consult externally scraped plots, and filter plots. 
- Receive notifications when a new plot becomes available. 
- View match scores between client preferences and available plots.
- Accept or reject matches to decide whether a plot becomes visible to the client.
- Set the Top 10 matches: you decide which plots the client will see.
- Track client preferences and activate new matches when a client updates their preferences. 

### What your client can do:
- Log in through the client login.
- View their personal dashboard with match scores per plot. 
- See the Top 10 best matches selected by your building company. 
- View match details: location, price, area, photos, total score.
- Adjust their preferences (budget, m², location, subdivision type, …).

## How to install the app?

1) Clone repository:
    ```text
    git clone
    https://github.com/A-D-DBS-application/web-application-2025-group-12.git
    cd web-application-2025-group-12
    ```

2) Virtual environment:

    - macOS / Linux:
    ```text
     python3 -m venv .venv
     source .venv/bin/activate
    ```

    - Windows (PowerShell):
    ```text
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
    ```

3) Install dependencies:
    ```text
    pip3 install --upgrade pip
    pip3 install -r requirements.txt
    ```

4) Create env. manually:
    ```text
    Contents: 
    DATABASE_URL=postgresql://postgres.dkqipvoxinwkvqawxkmx:ProjectGroundMD2%21@aws-1-eu-central-1.pooler.supabase.com:5432/postgres
    SECRET_KEY=supersecret-for-dev
    ```

5) VS Code setup (one-time):

     - Command Palette → “Python: Select Interpreter” → choose .venv.

     - Install the Python extension if someone doesn’t have it yet.

6) Run the app:

    - macOS / Linux:
    ```text
     python3 run.py
    ```

    - Windows:
    ```text
     python run.py
    ```


## Link to UI-prototype

https://www.figma.com/make/L7uPvepWneJHBqlXnq6imX/Web-Application-UI-Design?t=2i4nlD2i9Nq9FXR6-20&fullscreen=1

## Link to Kanban-board

https://miro.com/app/board/uXjVJ0CcO8w=/

## Link to audio/video recording of feedback sessions with partner 

- First meeting: https://drive.google.com/file/d/1VDLpL4u5b6rgSiR7dWZJFgXL_Ppsf_Jd/view?usp=sharing
- Second meeting: https://drive.google.com/file/d/1zyOU3aDmxZoA59DNjwgWavOvg83jHXea/view?usp=sharing

## Link to Render

https://web-application-2025-group-12-6.onrender.com

## Team

- Axl Hanssen
- Joos Van Lommel
- Floor Guldemont
- Tine Van Ryckeghem
- Marie-Justine Speybroek
