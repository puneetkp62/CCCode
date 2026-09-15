-- ============================================================
-- TechNova Imaging Systems Pvt Ltd
-- Employee Self Reflection Form — Database Setup
-- Run this script ONCE in SSMS before first use
-- Database: CORPHEALTH
-- ============================================================

USE CORPHEALTH;
GO

-- ------------------------------------------------------------
-- Table 1: reflection_submissions
-- One row per submitted form (employee + general answers)
-- ------------------------------------------------------------
IF NOT EXISTS (
    SELECT 1 FROM sys.objects
    WHERE object_id = OBJECT_ID(N'dbo.reflection_submissions')
    AND type = 'U'
)
BEGIN
    CREATE TABLE dbo.reflection_submissions (
        submission_id   INT IDENTITY(1,1)   NOT NULL PRIMARY KEY,
        emp_code        NVARCHAR(20)        NOT NULL,
        emp_name        NVARCHAR(200)       NOT NULL,
        role            NVARCHAR(300)           NULL,
        role_function   NVARCHAR(100)           NULL,
        band            NVARCHAR(10)        NOT NULL,
        team_leader     NVARCHAR(200)           NULL,
        division        NVARCHAR(100)           NULL,

        -- General Reflection answers (Part A)
        general_q1      NVARCHAR(MAX)           NULL,   -- Contributions / accomplishments
        general_q2      NVARCHAR(MAX)           NULL,   -- Work that gives energy
        general_q3      NVARCHAR(MAX)           NULL,   -- New learnings (last 3 yrs)
        general_q4      NVARCHAR(MAX)           NULL,   -- Challenges that contributed to growth
        general_q5      NVARCHAR(MAX)           NULL,   -- Most challenging work (last 1 yr)
        general_q6      NVARCHAR(MAX)           NULL,   -- Competencies to strengthen
        general_q7      NVARCHAR(MAX)           NULL,   -- Career direction (checkboxes, comma-sep)
        general_q8      NVARCHAR(MAX)           NULL,   -- Support / exposure needed
        general_q9      NVARCHAR(MAX)           NULL,   -- Mentor / coach preferences

        submitted_at    DATETIME            NOT NULL DEFAULT GETDATE()
    );

    PRINT 'Table dbo.reflection_submissions created.';
END
ELSE
    PRINT 'Table dbo.reflection_submissions already exists — skipped.';
GO

-- ------------------------------------------------------------
-- Table 2: competency_responses
-- One row per competency per submitted form (Part B answers)
-- ------------------------------------------------------------
IF NOT EXISTS (
    SELECT 1 FROM sys.objects
    WHERE object_id = OBJECT_ID(N'dbo.competency_responses')
    AND type = 'U'
)
BEGIN
    CREATE TABLE dbo.competency_responses (
        response_id     INT IDENTITY(1,1)   NOT NULL PRIMARY KEY,
        submission_id   INT                 NOT NULL
            REFERENCES dbo.reflection_submissions(submission_id)
            ON DELETE CASCADE,

        competency      NVARCHAR(200)           NULL,   -- e.g. Thinking
        attribute       NVARCHAR(200)           NULL,   -- e.g. Analytical Skills
        description     NVARCHAR(MAX)           NULL,   -- Competency definition
        indicator_text  NVARCHAR(MAX)           NULL,   -- Band-specific expected behaviour
        rating          INT                     NULL    CHECK (rating BETWEEN 0 AND 10),
        reflection_text NVARCHAR(MAX)           NULL    -- Employee's written reflection
    );

    PRINT 'Table dbo.competency_responses created.';
END
ELSE
    PRINT 'Table dbo.competency_responses already exists — skipped.';
GO

-- ------------------------------------------------------------
-- Useful queries for HR / admins
-- ------------------------------------------------------------

-- View all submissions with employee details:
-- SELECT s.submission_id, s.emp_code, s.emp_name, s.role_function,
--        s.band, s.submitted_at
-- FROM dbo.reflection_submissions s
-- ORDER BY s.submitted_at DESC;

-- View competency ratings for a specific submission:
-- SELECT r.competency, r.attribute, r.rating, r.reflection_text
-- FROM dbo.competency_responses r
-- WHERE r.submission_id = 1
-- ORDER BY r.competency, r.attribute;

-- Average rating per competency across all submissions:
-- SELECT r.competency, r.attribute,
--        COUNT(*) AS responses,
--        AVG(CAST(r.rating AS FLOAT)) AS avg_rating
-- FROM dbo.competency_responses r
-- GROUP BY r.competency, r.attribute
-- ORDER BY avg_rating DESC;

PRINT 'Setup complete. Both tables are ready.';
GO
