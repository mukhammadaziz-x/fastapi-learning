"""Models package - import all models so Base.metadata knows about them."""
from app.models.user import User
from app.models.subject import Subject
from app.models.group import Group, GroupMembership
from app.models.enrollment import Enrollment
from app.models.assignment import Assignment, AssignmentQuestion
from app.models.submission import Submission, SubmissionAnswer
from app.models.violation import FullscreenViolation
from app.models.feedback import Feedback
from app.models.leaderboard import LeaderboardCache

__all__ = [
    "User",
    "Subject",
    "Group", "GroupMembership",
    "Enrollment",
    "Assignment", "AssignmentQuestion",
    "Submission", "SubmissionAnswer",
    "FullscreenViolation",
    "Feedback",
    "LeaderboardCache",
]
