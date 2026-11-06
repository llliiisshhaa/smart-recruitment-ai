"""
Database Seeding Script for Smart Recruitment System.
Populates standard skills taxonomy (~40 skills) and interview question bank (~30 questions)
across multiple difficulty levels and skill categories.

Idempotent: Safe to execute multiple times without duplicating or corrupting records.
Security: Does NOT insert any users or credentials.
Resilience: Gracefully handles unreachable database connections with helpful diagnostic tips.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List

# Ensure backend directory is in sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select, text
from sqlalchemy.exc import OperationalError
from app.database import SessionLocal, engine
from app.models import Question, Skill


# ==============================================================================
# Seed Data: ~40 Standard Skills
# ==============================================================================
SKILLS_DATA: List[Dict[str, str]] = [
    # Programming Languages
    {"name": "python", "category": "Programming Language"},
    {"name": "java", "category": "Programming Language"},
    {"name": "javascript", "category": "Programming Language"},
    {"name": "typescript", "category": "Programming Language"},
    {"name": "c++", "category": "Programming Language"},
    {"name": "c#", "category": "Programming Language"},
    {"name": "go", "category": "Programming Language"},
    {"name": "rust", "category": "Programming Language"},
    {"name": "ruby", "category": "Programming Language"},
    {"name": "php", "category": "Programming Language"},
    {"name": "kotlin", "category": "Programming Language"},
    {"name": "swift", "category": "Programming Language"},

    # Web & Frontend / Backend Frameworks
    {"name": "react", "category": "Frontend Framework"},
    {"name": "vue.js", "category": "Frontend Framework"},
    {"name": "angular", "category": "Frontend Framework"},
    {"name": "next.js", "category": "Web Framework"},
    {"name": "node.js", "category": "Backend Runtime"},
    {"name": "fastapi", "category": "Backend Framework"},
    {"name": "django", "category": "Backend Framework"},
    {"name": "html5", "category": "Web Fundamentals"},
    {"name": "css3", "category": "Web Fundamentals"},
    {"name": "tailwind css", "category": "Styling Framework"},

    # Databases & Storage
    {"name": "sql", "category": "Database"},
    {"name": "postgresql", "category": "Database"},
    {"name": "mysql", "category": "Database"},
    {"name": "mongodb", "category": "NoSQL Database"},
    {"name": "redis", "category": "Caching & In-Memory"},
    {"name": "elasticsearch", "category": "Search & Analytics"},

    # DevOps, Cloud & Tools
    {"name": "docker", "category": "DevOps & Containerization"},
    {"name": "kubernetes", "category": "DevOps & Orchestration"},
    {"name": "aws", "category": "Cloud Platform"},
    {"name": "azure", "category": "Cloud Platform"},
    {"name": "git", "category": "Version Control"},
    {"name": "ci/cd", "category": "DevOps & Automation"},
    {"name": "linux", "category": "Operating System"},

    # AI, Machine Learning & Data
    {"name": "machine learning", "category": "Artificial Intelligence"},
    {"name": "deep learning", "category": "Artificial Intelligence"},
    {"name": "natural language processing", "category": "Artificial Intelligence"},
    {"name": "data analysis", "category": "Data Science"},
    {"name": "pandas", "category": "Data Science"},

    # Core Software Engineering & Soft Skills
    {"name": "system design", "category": "Architecture"},
    {"name": "problem solving", "category": "Engineering Fundamentals"},
    {"name": "communication", "category": "Soft Skill"},
    {"name": "agile", "category": "Methodology"},
]


# ==============================================================================
# Seed Data: 30 Interview Questions Across 5 Core Skills & 3 Difficulty Levels
# (2 questions per difficulty level per skill = 6 * 5 = 30 questions)
# ==============================================================================
QUESTIONS_DATA: List[Dict[str, Any]] = [
    # --------------------------------------------------------------------------
    # Skill: Python (6 questions: 2 Easy, 2 Medium, 2 Hard)
    # --------------------------------------------------------------------------
    {
        "skill": "python",
        "category": "technical",
        "difficulty": 1,
        "text": "What is the difference between mutable and immutable data types in Python? Provide examples of each.",
        "expected_points": [
            "Definition of mutability (can be modified in-place without changing memory identity)",
            "Examples of mutable types: list, dict, set",
            "Examples of immutable types: int, float, str, tuple, frozenset",
            "Implications when passing mutable objects as default function arguments",
        ],
    },
    {
        "skill": "python",
        "category": "technical",
        "difficulty": 1,
        "text": "How do list comprehensions work in Python, and how do they differ in syntax and readability from traditional for loops?",
        "expected_points": [
            "Syntax structure: [expression for item in iterable if condition]",
            "Readability and conciseness compared to loop append calls",
            "Slight performance advantage due to bytecode optimization",
            "When not to use (overly nested or complex logic reducing readability)",
        ],
    },
    {
        "skill": "python",
        "category": "technical",
        "difficulty": 2,
        "text": "Explain how Python generators work and the role of the 'yield' keyword. How do they help with memory efficiency?",
        "expected_points": [
            "Lazy evaluation / yielding items one-at-a-time on demand",
            "State preservation between yield statements (generator function protocol)",
            "Memory efficiency when processing large datasets or infinite streams vs full list in RAM",
            "Generator expressions and the next() built-in function",
        ],
    },
    {
        "skill": "python",
        "category": "technical",
        "difficulty": 2,
        "text": "What are Python decorators, and how are they implemented using closures or classes?",
        "expected_points": [
            "Higher-order functions that take a callable and return a wrapped callable",
            "Use of @decorator syntactic sugar",
            "Preserving metadata using functools.wraps",
            "Common use cases: logging, authorization, timing, caching",
        ],
    },
    {
        "skill": "python",
        "category": "technical",
        "difficulty": 3,
        "text": "Explain the Global Interpreter Lock (GIL) in CPython. How does it affect multithreaded CPU-bound versus I/O-bound applications, and what alternatives exist?",
        "expected_points": [
            "Mutex that prevents multiple native threads from executing Python bytecode simultaneously",
            "Impact: multithreading does not scale CPU-bound tasks across multiple cores",
            "Effect on I/O-bound tasks: GIL is released during system I/O waits, making threading effective",
            "Solutions: multiprocessing module, Celery distributed tasks, asyncio, C extensions",
        ],
    },
    {
        "skill": "python",
        "category": "technical",
        "difficulty": 3,
        "text": "How does Python's memory management work under the hood, specifically regarding reference counting and generational garbage collection?",
        "expected_points": [
            "Primary mechanism is reference counting (PyObject ob_refcnt)",
            "Deallocation occurs immediately when refcount reaches zero",
            "Generational GC (Gen 0, 1, 2) specifically detects and cleans up cyclical references",
            "Weak references (weakref) and the gc module inspection",
        ],
    },

    # --------------------------------------------------------------------------
    # Skill: SQL (6 questions: 2 Easy, 2 Medium, 2 Hard)
    # --------------------------------------------------------------------------
    {
        "skill": "sql",
        "category": "technical",
        "difficulty": 1,
        "text": "What is the difference between WHERE and HAVING clauses in SQL?",
        "expected_points": [
            "WHERE filters individual rows before aggregation occurs",
            "HAVING filters aggregated groups produced by GROUP BY",
            "WHERE cannot use aggregate functions (e.g., SUM, COUNT)",
            "Execution order: FROM -> WHERE -> GROUP BY -> HAVING -> SELECT",
        ],
    },
    {
        "skill": "sql",
        "category": "technical",
        "difficulty": 1,
        "text": "Explain the difference between INNER JOIN, LEFT OUTER JOIN, and FULL OUTER JOIN with practical examples.",
        "expected_points": [
            "INNER JOIN returns only rows with matching keys in both tables",
            "LEFT JOIN returns all rows from the left table and matched rows or NULLs from the right",
            "FULL OUTER JOIN returns all rows from both tables, filling unmatched columns with NULL",
            "Proper handling of NULL values when filtering joined columns",
        ],
    },
    {
        "skill": "sql",
        "category": "technical",
        "difficulty": 2,
        "text": "What are SQL window functions? Explain the purpose of the OVER clause, PARTITION BY, and ORDER BY within a window function.",
        "expected_points": [
            "Window functions calculate values across a set of rows without collapsing rows like GROUP BY",
            "OVER clause defines the calculation window",
            "PARTITION BY divides rows into calculation subsets",
            "Examples: ROW_NUMBER(), RANK(), DENSE_RANK(), LAG(), LEAD()",
        ],
    },
    {
        "skill": "sql",
        "category": "technical",
        "difficulty": 2,
        "text": "What is database indexing, how does a B-Tree index work, and what are the trade-offs of adding too many indexes?",
        "expected_points": [
            "Index is an auxiliary data structure speeding up SELECT and filter queries",
            "B-Tree index allows logarithmic O(log N) lookup, range scans, and sorting",
            "Trade-offs: write overhead on INSERT/UPDATE/DELETE because indexes must be updated",
            "Storage overhead for each secondary index",
        ],
    },
    {
        "skill": "sql",
        "category": "technical",
        "difficulty": 3,
        "text": "Explain database transaction isolation levels (Read Uncommitted, Read Committed, Repeatable Read, Serializable) and the concurrency anomalies they prevent.",
        "expected_points": [
            "Anomalies: dirty reads, non-repeatable reads, phantom reads, serialization anomalies",
            "Read Committed: prevents dirty reads (PostgreSQL default)",
            "Repeatable Read: prevents dirty and non-repeatable reads using snapshots (MVCC)",
            "Serializable: complete isolation simulating serial execution, prevents phantom reads",
            "Performance vs consistency trade-offs across isolation levels",
        ],
    },
    {
        "skill": "sql",
        "category": "technical",
        "difficulty": 3,
        "text": "How do you diagnose and optimize a slow-running SQL query in PostgreSQL? Walk through using EXPLAIN ANALYZE.",
        "expected_points": [
            "Using EXPLAIN (ANALYZE, BUFFERS) to view actual execution time vs planner estimates",
            "Identifying Seq Scan vs Index Scan / Bitmap Index Scan on large tables",
            "Examining join algorithms: Hash Join vs Nested Loop vs Merge Join",
            "Remedies: composite indexes, partial indexes, VACUUM/ANALYZE for updated statistics, query restructuring",
        ],
    },

    # --------------------------------------------------------------------------
    # Skill: React (6 questions: 2 Easy, 2 Medium, 2 Hard)
    # --------------------------------------------------------------------------
    {
        "skill": "react",
        "category": "technical",
        "difficulty": 1,
        "text": "What is the difference between props and state in React?",
        "expected_points": [
            "Props are inputs passed from parent to child, read-only and immutable by the child",
            "State is local component memory managed and modified via setter functions (useState)",
            "State updates trigger re-renders of the component and its children",
            "Unidirectional data flow in React",
        ],
    },
    {
        "skill": "react",
        "category": "technical",
        "difficulty": 1,
        "text": "Why does React require keys when rendering lists, and what problems occur if array indexes are used as keys?",
        "expected_points": [
            "Keys help React's virtual DOM reconciliation identify which items have changed, added, or removed",
            "Enables minimal DOM mutations rather than re-rendering the entire list",
            "Index as key causes bugs when items are reordered, inserted, or deleted (state attached to wrong index)",
            "Keys should be unique and stable identifiers (e.g., database IDs)",
        ],
    },
    {
        "skill": "react",
        "category": "technical",
        "difficulty": 2,
        "text": "Explain the lifecycle and dependency array behavior of the useEffect hook. How and when is the cleanup function executed?",
        "expected_points": [
            "No dependencies: runs after every render",
            "Empty array []: runs once after initial mount",
            "With dependencies [a, b]: runs after render only if a dependency changed value",
            "Cleanup function runs before re-running the effect and upon component unmount (cancelling timers, subscriptions)",
        ],
    },
    {
        "skill": "react",
        "category": "technical",
        "difficulty": 2,
        "text": "Compare React Context API with state management libraries like Redux or Zustand. When should you use which?",
        "expected_points": [
            "Context API: built-in, great for low-velocity global state (themes, authenticated user profile, locale)",
            "Context re-render caveat: all consumers re-render when context value object changes",
            "External stores (Zustand/Redux): fine-grained selector subscriptions preventing unnecessary renders",
            "Middleware, devtools, and time-travel debugging in dedicated state libraries",
        ],
    },
    {
        "skill": "react",
        "category": "technical",
        "difficulty": 3,
        "text": "Explain React's Fiber architecture and Concurrent Mode. How does cooperative scheduling and time-slicing improve UI responsiveness?",
        "expected_points": [
            "Fiber is a rewrite of reconciliation from synchronous call-stack recursion to cooperative linked-list tree",
            "Allows pausing, prioritizing, aborting, and resuming render work based on user input urgency",
            "Time-slicing keeps the main thread responsive during expensive renders",
            "Hooks like useTransition and useDeferredValue enabling concurrent interruptible rendering",
        ],
    },
    {
        "skill": "react",
        "category": "technical",
        "difficulty": 3,
        "text": "How do you detect and resolve performance bottlenecks caused by excessive re-renders in a large React application?",
        "expected_points": [
            "Using React DevTools Profiler to identify components re-rendering frequently and highlight render triggers",
            "Memoization strategies: React.memo, useMemo for heavy calculations, useCallback for stable function references",
            "Component composition techniques (moving state down, lifting content up as children)",
            "Virtualization for rendering large tabular or list datasets (e.g., tanstack-virtual, react-window)",
        ],
    },

    # --------------------------------------------------------------------------
    # Skill: Machine Learning (6 questions: 2 Easy, 2 Medium, 2 Hard)
    # --------------------------------------------------------------------------
    {
        "skill": "machine learning",
        "category": "technical",
        "difficulty": 1,
        "text": "Explain the difference between supervised, unsupervised, and reinforcement learning with real-world examples.",
        "expected_points": [
            "Supervised: learns from labeled input-target pairs (e.g., spam detection, price prediction)",
            "Unsupervised: discovers hidden patterns in unlabeled data (e.g., customer segmentation via k-means)",
            "Reinforcement: agent learns optimal policy through trial-and-error rewards/penalties in an environment",
            "Key distinction in supervision feedback loops",
        ],
    },
    {
        "skill": "machine learning",
        "category": "technical",
        "difficulty": 1,
        "text": "What is the difference between classification and regression tasks in machine learning? Name common metrics for each.",
        "expected_points": [
            "Classification predicts discrete categorical labels (binary or multiclass)",
            "Regression predicts continuous numeric values",
            "Classification metrics: Accuracy, Precision, Recall, F1-Score, ROC-AUC",
            "Regression metrics: Mean Squared Error (MSE), RMSE, Mean Absolute Error (MAE), R-squared",
        ],
    },
    {
        "skill": "machine learning",
        "category": "technical",
        "difficulty": 2,
        "text": "Explain the bias-variance tradeoff. What symptoms indicate high bias versus high variance, and how do you mitigate each?",
        "expected_points": [
            "High bias: underfitting, model too simple, high error on both train and test sets",
            "High variance: overfitting, model memorizes noise, low training error but high test error",
            "Mitigating high bias: more complex model, engineer additional features, decrease regularization",
            "Mitigating high variance: add regularization (L1/L2), collect more data, feature selection, ensemble methods",
        ],
    },
    {
        "skill": "machine learning",
        "category": "technical",
        "difficulty": 2,
        "text": "What is cross-validation, why is K-fold preferred over a single train/test split, and when should you use Stratified K-Fold?",
        "expected_points": [
            "Splits dataset into K equal partitions; rotates training on K-1 folds and validating on the remaining fold",
            "Provides more reliable generalization estimate with variance across folds",
            "Stratified K-fold ensures each fold maintains the same class proportion as the original dataset",
            "Crucial for imbalanced classification problems",
        ],
    },
    {
        "skill": "machine learning",
        "category": "technical",
        "difficulty": 3,
        "text": "Explain the Transformer architecture self-attention mechanism. Why does self-attention scale quadratically with sequence length, and what optimizations address this?",
        "expected_points": [
            "Query, Key, Value matrix projections: Attention(Q, K, V) = softmax(Q K^T / sqrt(d_k)) * V",
            "Computes pairwise relationships across all tokens simultaneously without recurrence",
            "O(N^2) complexity arises from the N x N attention weight matrix for sequence length N",
            "Optimizations: FlashAttention (tiling, SRAM optimization), sparse attention, sliding window attention, linear attention",
        ],
    },
    {
        "skill": "machine learning",
        "category": "technical",
        "difficulty": 3,
        "text": "How do you detect, monitor, and mitigate data drift and concept drift in a production machine learning system?",
        "expected_points": [
            "Data drift (covariate shift): input distribution P(X) changes while P(Y|X) remains stable",
            "Concept drift: relationship between features and target P(Y|X) changes over time",
            "Detection statistical tests: Population Stability Index (PSI), Kolmogorov-Smirnov test, Wasserstein distance",
            "Mitigation: automated retraining pipelines, canary rollouts, human-in-the-loop fallback, shadow models",
        ],
    },

    # --------------------------------------------------------------------------
    # Skill: Communication (6 questions: 2 Easy, 2 Medium, 2 Hard)
    # --------------------------------------------------------------------------
    {
        "skill": "communication",
        "category": "behavioral",
        "difficulty": 1,
        "text": "Describe a situation where you had to explain a complex technical concept to a non-technical stakeholder. How did you ensure understanding?",
        "expected_points": [
            "STAR method (Situation, Task, Action, Result)",
            "Avoiding jargon, acronyms, and low-level implementation details",
            "Using relatable analogies and visual aids or simplified diagrams",
            "Checking for comprehension and actively soliciting questions",
        ],
    },
    {
        "skill": "communication",
        "category": "behavioral",
        "difficulty": 1,
        "text": "How do you structure written communication when opening a Pull Request or writing technical design notes for team members?",
        "expected_points": [
            "Clear title and executive summary explaining the 'Why' behind the change",
            "Bullet points summarizing key architectural decisions or tradeoffs",
            "Testing instructions and proof of verification (logs, screenshots)",
            "Linking relevant issue tracker tickets or design documents",
        ],
    },
    {
        "skill": "communication",
        "category": "situational",
        "difficulty": 2,
        "text": "How do you handle a situation where you strongly disagree with an architectural decision made by a senior colleague or tech lead?",
        "expected_points": [
            "Active listening to fully understand the rationale behind the proposal",
            "Focusing on data, user impact, benchmarks, and objective tradeoffs rather than personal preference",
            "Proposing alternatives constructively in private or collaborative design reviews",
            "Commitment principle: disagree and commit once a team consensus or final decision is reached",
        ],
    },
    {
        "skill": "communication",
        "category": "situational",
        "difficulty": 2,
        "text": "You realize a critical feature you committed to deliver by sprint end will be delayed. How and when do you communicate this to your team and manager?",
        "expected_points": [
            "Communicate proactively and early as soon as the delay risk is identified (never at deadline)",
            "Clearly explain root causes without shifting blame",
            "Present mitigation options (descoping non-essential items, revised timeline, requesting pairing assistance)",
            "Adjust sprint goals collaboratively with product owner",
        ],
    },
    {
        "skill": "communication",
        "category": "situational",
        "difficulty": 3,
        "text": "During a high-severity production outage, how do you manage incident communication across engineering, customer support, and executive leadership simultaneously?",
        "expected_points": [
            "Designate dedicated incident roles: incident commander vs communications lead",
            "Separate technical triage channel from public status updates to avoid engineer distraction",
            "Publish regular, predictable updates (e.g. every 15-30 minutes) even if status is unchanged",
            "Blameless post-mortem retrospective documenting timeline, root cause, and preventative action items",
        ],
    },
    {
        "skill": "communication",
        "category": "behavioral",
        "difficulty": 3,
        "text": "Tell me about a time you had to align multiple cross-functional teams with conflicting priorities toward a single strategic technical migration.",
        "expected_points": [
            "Identifying shared business goals and framing the migration in terms of organizational value",
            "Creating transparent roadmaps, dependency graphs, and phased migration milestones",
            "Addressing individual team concerns (e.g. bandwidth, SLA risks) with dedicated enablement tools",
            "Maintaining regular alignment syncs and celebrating incremental milestones",
        ],
    },
]


def check_database_connectivity() -> bool:
    """
    Verifies that the database is reachable before attempting data seeding.
    Prints helpful troubleshooting messages if the connection fails.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except OperationalError as exc:
        print("\n" + "=" * 70, file=sys.stderr)
        print("[DATABASE ERROR] Could not establish a connection to PostgreSQL.", file=sys.stderr)
        print(f"Error details: {exc}", file=sys.stderr)
        print("\nTroubleshooting tips for students:", file=sys.stderr)
        print(" 1. Ensure PostgreSQL is running locally on your system.", file=sys.stderr)
        print(" 2. Verify DATABASE_URL in your .env file matches your credentials.", file=sys.stderr)
        print(" 3. Example format: postgresql://<user>:<password>@localhost:5432/<dbname>", file=sys.stderr)
        print("=" * 70 + "\n", file=sys.stderr)
        return False
    except Exception as exc:
        print(f"[UNEXPECTED ERROR] An error occurred while testing DB connection: {exc}", file=sys.stderr)
        return False


def seed_skills(session) -> Dict[str, int]:
    """
    Seeds skills idempotently. Returns a mapping of skill_name -> skill_id.
    """
    print(f"Seeding {len(SKILLS_DATA)} skills...")
    created_count = 0
    existing_count = 0
    skill_map: Dict[str, int] = {}

    for item in SKILLS_DATA:
        normalized_name = item["name"].strip().lower()
        stmt = select(Skill).where(Skill.name == normalized_name)
        existing = session.execute(stmt).scalar_one_or_none()

        if existing:
            # Update category if needed
            if existing.category != item["category"]:
                existing.category = item["category"]
            skill_map[normalized_name] = existing.id
            existing_count += 1
        else:
            new_skill = Skill(
                name=normalized_name,
                category=item["category"],
            )
            session.add(new_skill)
            session.flush()  # Flush to obtain generated primary key
            skill_map[normalized_name] = new_skill.id
            created_count += 1

    session.commit()
    print(f"  -> Skills: {created_count} created, {existing_count} already existed. Total mapped: {len(skill_map)}")
    return skill_map


def seed_questions(session, skill_map: Dict[str, int]) -> None:
    """
    Seeds questions idempotently using (skill_id, text) as uniqueness key.
    """
    print(f"\nSeeding {len(QUESTIONS_DATA)} sample interview questions across 5 core skills...")
    created_count = 0
    existing_count = 0

    for q_data in QUESTIONS_DATA:
        skill_name = q_data["skill"].strip().lower()
        skill_id = skill_map.get(skill_name)
        if not skill_id:
            print(f"  [WARN] Skill '{skill_name}' not found in taxonomy. Skipping question.", file=sys.stderr)
            continue

        stmt = select(Question).where(
            Question.skill_id == skill_id,
            Question.text == q_data["text"],
        )
        existing = session.execute(stmt).scalar_one_or_none()

        if existing:
            # Update fields to ensure latest expected_points and difficulty
            existing.category = q_data["category"]
            existing.difficulty = q_data["difficulty"]
            existing.expected_points = q_data["expected_points"]
            existing.source = "bank"
            existing_count += 1
        else:
            new_q = Question(
                skill_id=skill_id,
                category=q_data["category"],
                difficulty=q_data["difficulty"],
                text=q_data["text"],
                expected_points=q_data["expected_points"],
                source="bank",
            )
            session.add(new_q)
            created_count += 1

    session.commit()
    print(f"  -> Questions: {created_count} created, {existing_count} already existed.")


def main():
    """Main execution entrypoint for data seeding."""
    print("=" * 60)
    print("Smart Recruitment System - Database Seed Script")
    print("=" * 60)

    # 1. Check database connectivity
    if not check_database_connectivity():
        sys.exit(1)

    # 2. Execute idempotent seeding inside a database session
    session = SessionLocal()
    try:
        skill_map = seed_skills(session)
        seed_questions(session, skill_map)
        print("\nDatabase seeding completed successfully!")
        print("Note: No user credentials or passwords were created.")
        print("=" * 60)
    except Exception as exc:
        session.rollback()
        print(f"\n[ERROR] An error occurred during database seeding: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
