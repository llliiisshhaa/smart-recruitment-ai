"""
Interview, Question, and Evaluation Models.
Defines the AI interview lifecycle: curated/generated questions, live interview sessions,
candidate answers (text or voice), rubric evaluations, aggregated skill assessments,
and candidate performance reports.
"""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Question(Base):
    """
    Question bank and AI-generated interview questions.
    Categorized by skill and difficulty rating (1=Junior, 2=Mid, 3=Senior).
    """

    __tablename__ = "questions"

    # Primary key identifier
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Skill being evaluated by this question
    skill_id = Column(
        Integer,
        ForeignKey("skills.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Question type: technical, behavioral, situational, or resume_based
    category = Column(String(50), nullable=False)

    # Difficulty scale (1 to 3)
    difficulty = Column(Integer, nullable=False)

    # Question prompt text asked to the candidate
    text = Column(Text, nullable=False)

    # Expected key points or evaluation criteria stored as JSON
    expected_points = Column(JSONB().with_variant(JSON, "sqlite"), nullable=True)

    # Origin of question: curated bank or AI generated dynamically
    source = Column(String(50), default="bank", nullable=False)

    # Timestamp when question was created
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Check constraints on category, difficulty, and source
    __table_args__ = (
        CheckConstraint(
            "category IN ('technical', 'behavioral', 'situational', 'resume_based')",
            name="check_question_category",
        ),
        CheckConstraint(
            "difficulty >= 1 AND difficulty <= 3",
            name="check_question_difficulty",
        ),
        CheckConstraint(
            "source IN ('bank', 'llm')",
            name="check_question_source",
        ),
    )

    # Relationships
    skill = relationship("Skill", back_populates="questions")
    interview_questions = relationship("InterviewQuestion", back_populates="question")

    def __repr__(self) -> str:
        return f"<Question id={self.id} skill_id={self.skill_id} diff={self.difficulty} source='{self.source}'>"


class Interview(Base):
    """
    Virtual interview session linked to a candidate's job application.
    Tracks interview status, chosen language, timestamps, and live session state.
    """

    __tablename__ = "interviews"

    # Primary key identifier
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Application being interviewed for
    application_id = Column(
        Integer,
        ForeignKey("applications.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Interview session status: scheduled, in_progress, completed
    status = Column(String(50), default="scheduled", nullable=False)

    # Communication language for the interview (e.g., 'en', 'es', 'fr')
    language = Column(String(50), default="en", nullable=False)

    # Timestamp when interview was started by candidate
    started_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamp when interview was concluded
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # State machine JSON tracking current question, turn counter, and agent context
    state = Column(JSONB().with_variant(JSON, "sqlite"), nullable=True)

    # Timestamp when interview was created
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Check constraint for valid interview lifecycle status
    __table_args__ = (
        CheckConstraint(
            "status IN ('scheduled', 'in_progress', 'completed')",
            name="check_interview_status",
        ),
    )

    # Relationships
    application = relationship("Application", back_populates="interviews")
    questions = relationship(
        "InterviewQuestion",
        back_populates="interview",
        cascade="all, delete-orphan",
        order_by="InterviewQuestion.order_no",
    )
    skill_assessments = relationship(
        "SkillAssessment",
        back_populates="interview",
        cascade="all, delete-orphan",
    )
    report = relationship(
        "Report",
        back_populates="interview",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Interview id={self.id} application_id={self.application_id} status='{self.status}'>"


class InterviewQuestion(Base):
    """
    Specific question posed to a candidate during an interview session.
    Can reference a bank question or be a dynamic followup to a previous answer.
    """

    __tablename__ = "interview_questions"

    # Primary key identifier
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Interview session this question belongs to
    interview_id = Column(
        Integer,
        ForeignKey("interviews.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Reference to original question from bank (nullable for LLM-generated followups)
    question_id = Column(
        Integer,
        ForeignKey("questions.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    # Text of the question presented to the candidate
    question_text = Column(Text, nullable=False)

    # Skill evaluated by this question (nullable if general)
    skill_id = Column(
        Integer,
        ForeignKey("skills.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    # Difficulty rating of the asked question (1-3)
    difficulty = Column(Integer, nullable=False)

    # Sequential order number in the interview (1, 2, 3...)
    order_no = Column(Integer, default=1, nullable=False)

    # True if this question was generated dynamically as a followup
    is_followup = Column(Boolean, default=False, nullable=False)

    # Parent question ID if this question is a followup to another question
    parent_id = Column(
        Integer,
        ForeignKey("interview_questions.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    # Timestamp when question was delivered to candidate
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    interview = relationship("Interview", back_populates="questions")
    question = relationship("Question", back_populates="interview_questions")
    skill = relationship("Skill")
    parent = relationship(
        "InterviewQuestion",
        remote_side=[id],
        backref="followups",
    )
    answer = relationship(
        "Answer",
        back_populates="interview_question",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<InterviewQuestion id={self.id} interview_id={self.interview_id} order={self.order_no}>"


class Answer(Base):
    """
    Candidate's submitted response to an interview question.
    Supports text and voice inputs, multilingual translation, and audio transcripts.
    """

    __tablename__ = "answers"

    # Primary key identifier
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Question answered by candidate (1:1 relationship)
    interview_question_id = Column(
        Integer,
        ForeignKey("interview_questions.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    # Raw transcript or text as entered by candidate
    original_text = Column(Text, nullable=False)

    # ISO language code detected from input (e.g. 'en', 'hi', 'es')
    detected_language = Column(String(50), nullable=True)

    # English translation if candidate responded in another language
    translated_text = Column(Text, nullable=True)

    # Input method used: text typing or voice speech-to-text
    input_mode = Column(String(50), default="text", nullable=False)

    # Timestamp when candidate submitted the answer
    answered_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Check constraint for valid input mode
    __table_args__ = (
        CheckConstraint(
            "input_mode IN ('text', 'voice')",
            name="check_answer_input_mode",
        ),
    )

    # Relationships
    interview_question = relationship("InterviewQuestion", back_populates="answer")
    evaluation = relationship(
        "Evaluation",
        back_populates="answer",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Answer id={self.id} question_id={self.interview_question_id} mode='{self.input_mode}'>"


class Evaluation(Base):
    """
    Multi-dimensional evaluation score for a candidate's answer.
    Scores technical accuracy, relevance, completeness, communication, and overall score (0-100).
    Allows manual recruiter score overrides with audit logging.
    """

    __tablename__ = "evaluations"

    # Primary key identifier
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Evaluated answer (1:1 relationship)
    answer_id = Column(
        Integer,
        ForeignKey("answers.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    # Technical correctness score (0.0 to 100.0)
    technical = Column(Float, nullable=False)

    # Relevance to the question prompt (0.0 to 100.0)
    relevance = Column(Float, nullable=False)

    # Completeness addressing all expected points (0.0 to 100.0)
    completeness = Column(Float, nullable=False)

    # Clarity and communication quality (0.0 to 100.0)
    communication = Column(Float, nullable=False)

    # Weighted aggregate score (0.0 to 100.0)
    total = Column(Float, nullable=False)

    # AI justification narrative explaining score breakdown
    justification = Column(Text, nullable=True)

    # Evaluator engine: AI llm or rule-based evaluator
    evaluator = Column(String(50), default="llm", nullable=False)

    # Optional human recruiter override total score (0.0 to 100.0)
    override_total = Column(Float, nullable=True)

    # Recruiter user who overrode the automated score
    override_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    # Justification note written by human reviewer explaining override
    override_note = Column(Text, nullable=True)

    # Timestamp when evaluation was generated
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Check constraints on numeric bounds (0-100) and evaluator type
    __table_args__ = (
        CheckConstraint("technical >= 0 AND technical <= 100", name="check_eval_technical"),
        CheckConstraint("relevance >= 0 AND relevance <= 100", name="check_eval_relevance"),
        CheckConstraint("completeness >= 0 AND completeness <= 100", name="check_eval_completeness"),
        CheckConstraint("communication >= 0 AND communication <= 100", name="check_eval_communication"),
        CheckConstraint("total >= 0 AND total <= 100", name="check_eval_total"),
        CheckConstraint("evaluator IN ('llm', 'rule')", name="check_evaluator_type"),
        CheckConstraint(
            "override_total IS NULL OR (override_total >= 0 AND override_total <= 100)",
            name="check_eval_override_total",
        ),
    )

    # Relationships
    answer = relationship("Answer", back_populates="evaluation")
    override_reviewer = relationship("User", foreign_keys=[override_by])

    def __repr__(self) -> str:
        return f"<Evaluation id={self.id} answer_id={self.answer_id} total={self.total}>"


class SkillAssessment(Base):
    """
    Aggregated skill proficiency summary for a candidate across an entire interview.
    Compares claimed skills from resume against demonstrated interview performance.
    """

    __tablename__ = "skill_assessments"

    # Composite primary key: interview_id + skill_id
    interview_id = Column(
        Integer,
        ForeignKey("interviews.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    skill_id = Column(
        Integer,
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

    # Whether candidate listed this skill on their submitted resume
    claimed_in_resume = Column(Boolean, default=False, nullable=False)

    # Average score achieved across questions testing this skill (0.0 to 100.0)
    avg_score = Column(Float, nullable=True)

    # Verification label assessing mastery vs claim
    label = Column(String(50), nullable=False)

    # Timestamp when assessment was computed
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Check constraint on valid assessment labels
    __table_args__ = (
        CheckConstraint(
            "label IN ('confirmed', 'weak', 'not_demonstrated', 'needs_verification', 'missing_from_resume')",
            name="check_assessment_label",
        ),
    )

    # Relationships
    interview = relationship("Interview", back_populates="skill_assessments")
    skill = relationship("Skill", back_populates="skill_assessments")

    def __repr__(self) -> str:
        return f"<SkillAssessment interview_id={self.interview_id} skill_id={self.skill_id} label='{self.label}'>"


class Report(Base):
    """
    Comprehensive candidate assessment report generated at interview completion.
    Stores structured summary JSON and disk path to generated PDF report.
    """

    __tablename__ = "reports"

    # Primary key identifier
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Interview session analyzed in this report (1:1 relationship)
    interview_id = Column(
        Integer,
        ForeignKey("interviews.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    # Structured summary JSON (strengths, growth areas, recommendations)
    summary_json = Column(JSONB().with_variant(JSON, "sqlite"), nullable=True)

    # File path to generated PDF evaluation report
    pdf_path = Column(String(500), nullable=True)

    # Timestamp when report was generated
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    interview = relationship("Interview", back_populates="report")

    def __repr__(self) -> str:
        return f"<Report id={self.id} interview_id={self.interview_id}>"
