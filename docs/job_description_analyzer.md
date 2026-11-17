# Job Description Analyzer (Stage 9)

A deterministic, rule-based analysis engine designed to assist recruiters during job posting creation and editing without relying on external LLMs or third-party APIs.

---

## 1. Input

The analyzer is triggered on-demand by authenticated recruiters via the `POST /jobs/analyze` endpoint.

- **Payload (`JobAnalyzeRequest`)**:
  - `title` *(string, optional, max 150 chars)*: The proposed job title (e.g., `"Senior Backend Engineer"`).
  - `description` *(string, required, min 1 char, max 10,000 chars)*: The raw text of the job description outlining duties, requirements, and company context.
- **Frontend Trigger**:
  - In `JobModal.jsx`, an "Analyze description" button is active once the recruiter has entered at least 30 characters in the description textarea.

---

## 2. Processing Pipeline

The analyzer runs entirely in-process using local deterministic rule engines, regular expressions, and the taxonomy dictionary:

1. **Skill Taxonomy Matching**:
   - Reuses canonical skills and the 60+ alias taxonomy dictionary from the resume parser (`app/ai/data/skill_aliases.json`).
   - Employs punctuation-safe, word-boundary regular expressions (`_build_skill_pattern`) to accurately detect skills like `C++`, `C#`, `.NET`, `Node.js`, and `CI/CD` while avoiding substring collisions (such as matching `Java` inside `JavaScript` or `Go` inside `Good`).
   - Identifies importance (`required` vs. `preferred`) by scanning surrounding syntactic cues (`must`, `required`, `essential`, `strong` vs. `preferred`, `plus`, `bonus`, `nice to have`) with clause-boundary distance penalties to prevent cross-clause false positives.
   - Captures concise, verbatim evidence excerpts surrounding each matched skill.

2. **Requirements Extraction**:
   - **Minimum Experience**: Regex patterns evaluate expressions like `"3+ years"`, `"3-5 years"`, `"minimum 4 yrs"`, `"at least 2 years"`, and `"fresher"` / `"entry level"` ($\rightarrow 0$ years), returning the lowest integer clamped between 0 and 40 years.
   - **Education Level**: Keyword matching identifies degrees hierarchically (`Doctorate / Ph.D.`, `Master's Degree`, `Bachelor's Degree`, `Associate Degree`, `High School Diploma`).

3. **Responsibilities Extraction**:
   - Locates role duties by detecting section headers (`Responsibilities`, `What You'll Do`, `Duties`, `Key Tasks`) or inline bullet symbols (`-`, `*`, `•`, numbered lists).
   - Normalizes whitespace, strips noise, and extracts up to 10 distinct responsibility statements.

4. **Fairness & Inclusivity Scanning**:
   - Scans against an anti-bias term database (`app/ai/data/biased_terms.json`) covering protected characteristics:
     - Age: e.g. `"young and energetic"`, `"digital native"`, `"recent graduate"`, `"mature candidate"`.
     - Gender: e.g. `"male candidate"`, `"female candidate"`, `"salesman"`, `"manpower"`, gender-coded terms (`"ninja"`, `"rockstar"`).
     - Marital Status: e.g. `"unmarried"`, `"single candidates only"`.
     - Nationality / Origin: e.g. `"native english speaker"`, `"us citizens only"`.
   - Avoids false positives by excluding bare ambiguous words (terms like `"bachelor"`, `"single"`, and `"mature"` in contexts such as `"Bachelor's degree in Computer Science"`, `"single sign-on"`, `"single-page application"`, or `"mature codebase"` produce zero warnings).
   - Generates constructive, neutral phrasing alternatives for every flagged term.

---

## 3. Output

Returns a structured `JobAnalyzeResponse`:

- `skills` *(List[JobSkillSuggestion])*:
  - `skill_id`: Database ID of the canonical taxonomy skill.
  - `name`: Canonical skill name.
  - `suggested_importance`: `"required"` or `"preferred"`.
  - `evidence_text`: Verbatim sentence excerpt from the description.
- `min_experience_years` *(Optional[int])*: Detected years requirement (or `null`).
- `education` *(Optional[str])*: Detected highest degree level (or `null`).
- `responsibilities` *(List[str])*: Extracted clean bullet items (up to 10).
- `fairness_warnings` *(List[FairnessWarning])*:
  - `matched_phrase`: The matched discriminatory or non-inclusive term.
  - `category`: Category classification (`age`, `gender`, `marital_status`, `nationality`).
  - `suggested_rewrite`: Recommended inclusive replacement.
- `meta` *(Dict[str, Any])*: Includes `analyzer_version` (`"1.0.0"`), `analyzed_at` ISO timestamp, and extraction counts.

---

## 4. Validation

- **Role Authorization**: Protected with `require_roles("recruiter")`. Candidates receive HTTP 403 Forbidden; unauthenticated requests receive HTTP 401 Unauthorized.
- **Input Bounds**: `description` must contain between 1 and 10,000 characters; whitespace-only strings are rejected with HTTP 422 Unprocessable Content.
- **Stateless Persistence**: The analysis does not write to `jobs` or `job_skills` tables. A lightweight `JOB_DESCRIPTION_ANALYZED` audit row records character lengths and suggestion counts without logging raw description text.
- **Frontend Validation**: Double-clicks and in-flight requests are blocked via disabled states and loading spinners.

---

## 5. Fallback Behaviour

- **Resilience**: The analyzer safely handles noisy, repetitive, empty, or foreign-language input without raising unhandled exceptions.
- **No Extracted Match**: If no taxonomy skills, experience phrases, or bullet points are detected, the analyzer returns empty lists and `null` values; the UI gracefully informs the recruiter (`"No taxonomy skills matched in the description"`).
- **Human-in-the-Loop Safeguard**:
  - The UI presents suggestions in an inspection panel bearing the explicit notice:
    > *"Suggestions are generated by rules, not by a model. Review before applying."*
  - Nothing is applied automatically. The recruiter retains full discretion to inspect evidence, toggle importance, add specific skills, or apply extracted fields before submitting the job posting.
