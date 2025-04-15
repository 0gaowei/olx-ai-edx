"""用户模型相关类，包括用户配置文件等"""

from typing import List, Dict, Optional
from .skill import Skill


class UserProfile:
    """用户配置文件，包含个人信息、技能水平和学习目标"""

    def __init__(self, name: str, skill_level: Optional[str] = None, learning_goals: Skill = None):
        """初始化用户配置文件

        Args:
            name: 用户名称
            skill_level: 技能水平 (初级/中级/高级)
            learning_goals: 学习目标列表
        """
        self.name = name
        self.skill_level = skill_level
        self.learning_goals = learning_goals

    def __str__(self) -> str:
        return f"UserProfile(name={self.name}, skill_level={self.skill_level}, learning_goals={self.learning_goals})"
