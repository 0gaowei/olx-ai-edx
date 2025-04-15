"""课程生成器生成包"""

from .ai_gen_content import AIGenerator
from .course_manager import CourseGenerationManager
from .user_interaction import UserInteractionManager

__all__ = [
    'AIGenerator',
    'CourseGenerationManager',
    'UserInteractionManager'
]
