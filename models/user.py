"""用户模型相关类，包括用户配置文件等"""

from typing import List, Dict, Optional


class UserProfile:
    """用户配置文件，包含个人信息、技能水平和学习目标"""

    def __init__(self, name: str, skill_level: Optional[str] = None, learning_goals: Optional[List[str]] = None):
        """初始化用户配置文件

        Args:
            name: 用户名称
            skill_level: 技能水平 (初级/中级/高级)
            learning_goals: 学习目标列表
        """
        self.name = name
        self.skill_level = skill_level
        self.learning_goals = learning_goals or []

    def assess_skill_level(self, answers: Dict[str, bool]) -> str:
        """根据测评问题答案评估用户技能水平

        Args:
            answers: 测评问题答案字典 {问题ID: 是否正确}

        Returns:
            评估的技能水平 (初级/中级/高级)
        """
        correct_count = sum(answers.values())

        if correct_count <= 3:
            self.skill_level = "初级"
        elif correct_count <= 7:
            self.skill_level = "中级"
        else:
            self.skill_level = "高级"

        return self.skill_level

    def add_learning_goal(self, goal: str) -> None:
        """添加学习目标

        Args:
            goal: 要添加的学习目标
        """
        if goal not in self.learning_goals:
            self.learning_goals.append(goal)

    def __str__(self) -> str:
        return f"UserProfile(name={self.name}, skill_level={self.skill_level}, goals={self.learning_goals})"
