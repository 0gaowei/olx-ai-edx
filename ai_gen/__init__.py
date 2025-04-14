"""课程生成器生成包"""

from .ai_gen_content import AIGenerator
from .course_manager import CourseGenerationManager

__all__ = [
    'AIGenerator',
    'CourseGenerationManager'
]
