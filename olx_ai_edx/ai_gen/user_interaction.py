import os
from typing import List, Dict, Any, Tuple
from ..models import UserProfile
from ..models import Skill
from .ai_gen_content import AIGenerator

class UserInteractionManager:
    def __init__(self, max_iterations: int = 1, aigenerator: AIGenerator = None):
        """初始化用户交互管理器"""
        self.max_iterations = max_iterations
        self.aigenerator = aigenerator or AIGenerator()
    
    def collect_basic_info(self) -> Tuple[str, str]:
        """收集用户基本信息"""
        nickname = input("请输入您的昵称: ")
        skill_name = input("请输入您想学习的技能名称(如'Python 编程'): ")
        return nickname, skill_name
    
    def assess_user_level(self, skill_name: str) -> Dict[str, Any]:
        """通过AI生成的问题评估用户水平"""
        print(f"\n让我们评估您在{skill_name}方面的水平和学习目标...\n")
        
        try:
            # 调用ai_gen_content.py中的函数生成评估问题
            print("正在生成评估问题...")
            assessment_questions = self.aigenerator.generate_assessment_questions(skill_name)
            print(f"以下是{skill_name}的评估问题:\n{assessment_questions}")

            # 收集用户回答
            user_responses = []
            for question in assessment_questions:
                response = input(f"{question} ")
                user_responses.append({"question": question, "answer": response})
            
            # 调用ai_gen_content.py中的函数分析用户回答
            print("正在分析您的回答...")
            assessment_result = self.aigenerator.analyze_user_responses(skill_name, user_responses)
            return assessment_result
            
        except Exception as e:
            print(f"评估过程中出错: {e}")
            # 返回默认评估结果
            return {
                "level": "beginner",
                "explanation": f"由于评估过程中出现错误，默认将您视为{skill_name}的初学者。",
                "objectives": [
                    f"掌握{skill_name}的基础概念和术语",
                    f"完成{skill_name}的入门级练习和项目",
                    f"理解{skill_name}的核心原理",
                    f"能够应用{skill_name}解决简单问题",
                    f"建立{skill_name}的学习习惯和方法"
                ],
                "learning_path": f"从基础概念开始，通过实践项目逐步掌握{skill_name}技能。"
            }
    
    def create_user_profile(self, nickname: str, level: str, skill_name: str, learning_goals: Skill = None) -> UserProfile:
        """创建用户画像"""
        if not learning_goals:
            learning_goals = Skill(name=skill_name, description=f"{skill_name}的技能")
        
        user_profile = UserProfile(
            name=nickname,
            skill_level=level,
            learning_goals=learning_goals
        )
        
        return user_profile
