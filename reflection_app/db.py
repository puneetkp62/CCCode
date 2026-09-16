try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False

import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={os.getenv('DB_SERVER', '')};"
    f"DATABASE={os.getenv('DB_NAME', '')};"
    f"UID={os.getenv('DB_USER', '')};"
    f"PWD={os.getenv('DB_PASSWORD', '')};"
    f"Encrypt={os.getenv('DB_ENCRYPT', 'yes')};"
    f"TrustServerCertificate={os.getenv('DB_TRUST_CERT', 'yes')};"
)


def get_connection():
    if not PYODBC_AVAILABLE:
        raise RuntimeError(
            "pyodbc / ODBC Driver 17 not installed on this machine. "
            "Deploy on the organisation server where the driver is available."
        )
    return pyodbc.connect(CONN_STR)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='reflection_submissions' AND xtype='U')
    CREATE TABLE reflection_submissions (
        submission_id   INT IDENTITY(1,1) PRIMARY KEY,
        emp_code        NVARCHAR(20),
        emp_name        NVARCHAR(200),
        role            NVARCHAR(300),
        role_function   NVARCHAR(100),
        band            NVARCHAR(10),
        team_leader     NVARCHAR(200),
        division        NVARCHAR(100),
        general_q1      NVARCHAR(MAX),
        general_q2      NVARCHAR(MAX),
        general_q3      NVARCHAR(MAX),
        general_q4      NVARCHAR(MAX),
        general_q5      NVARCHAR(MAX),
        general_q6      NVARCHAR(MAX),
        general_q7      NVARCHAR(MAX),
        general_q8      NVARCHAR(MAX),
        general_q9      NVARCHAR(MAX),
        submitted_at    DATETIME DEFAULT GETDATE()
    )
    """)

    cur.execute("""
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='competency_responses' AND xtype='U')
    CREATE TABLE competency_responses (
        response_id      INT IDENTITY(1,1) PRIMARY KEY,
        submission_id    INT REFERENCES reflection_submissions(submission_id),
        competency       NVARCHAR(200),
        attribute        NVARCHAR(200),
        description      NVARCHAR(MAX),
        indicator_text   NVARCHAR(MAX),
        rating           INT,
        reflection_text  NVARCHAR(MAX)
    )
    """)

    conn.commit()
    cur.close()
    conn.close()


def save_submission(session_data):
    conn = get_connection()
    cur = conn.cursor()

    general = session_data.get('general_answers', {})
    q7 = general.get('q7', [])
    if isinstance(q7, list):
        q7 = '; '.join(q7)

    cur.execute("""
        INSERT INTO reflection_submissions
            (emp_code, emp_name, role, role_function, band, team_leader, division,
             general_q1, general_q2, general_q3, general_q4, general_q5,
             general_q6, general_q7, general_q8, general_q9)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        session_data.get('emp_code', ''),
        session_data.get('emp_name', ''),
        session_data.get('role', ''),
        session_data.get('role_function', ''),
        session_data.get('band', ''),
        session_data.get('team_leader', ''),
        session_data.get('division', ''),
        general.get('q1', ''), general.get('q2', ''), general.get('q3', ''),
        general.get('q4', ''), general.get('q5', ''), general.get('q6', ''),
        q7, general.get('q8', ''), general.get('q9', ''),
    ))

    cur.execute("SELECT @@IDENTITY")
    submission_id = int(cur.fetchone()[0])

    comp_answers = session_data.get('competency_answers', {})
    for comp in comp_answers.values():
        cur.execute("""
            INSERT INTO competency_responses
                (submission_id, competency, attribute, description,
                 indicator_text, rating, reflection_text)
            VALUES (?,?,?,?,?,?,?)
        """, (
            submission_id,
            comp.get('competency', ''),
            comp.get('attribute', ''),
            comp.get('description', ''),
            comp.get('indicator', ''),
            int(comp.get('rating', 0)),
            comp.get('reflection', ''),
        ))

    conn.commit()
    cur.close()
    conn.close()
    return submission_id
