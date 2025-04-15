import os
import json
from typing import List, Dict, Any
import openai  # 或您使用的其他LLM API库
from ..models import UserProfile
from ..models import Skill

class UserInteractionManager:
    def __init__(self, api_key=None):
        """初始化用户交互管理器"""
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = "glm-4-long"  # 或您使用的其他模型
        self.temperature = 0.7
    
    def collect_basic_info(self):
        """收集用户基本信息"""
        nickname = input("请输入您的昵称: ")
        skill_name = input("请输入您想学习的技能名称(如'Python 编程'): ")
        return nickname, skill_name
    
    def assess_user_level(self, skill_name: str) -> Dict[str, Any]:
        """通过AI生成的问题评估用户水平"""
        print(f"\n让我们评估您在{skill_name}方面的水平和学习目标...\n")
        
        # 生成评估问题
        assessment_questions = self._generate_assessment_questions(skill_name)
        
        # 收集用户回答
        user_responses = []
        for question in assessment_questions:
            response = input(f"{question} ")
            user_responses.append({"question": question, "answer": response})
        
        # 分析用户回答
        assessment_result = self._analyze_user_responses(skill_name, user_responses)
        return assessment_result
    
    def _generate_assessment_questions(self, skill_name: str) -> List[str]:
        """使用LLM生成针对特定技能的评估问题"""
        prompt = f"""
        你是一位教育评估专家。请为评估用户在"{skill_name}"领域的水平生成5个有效问题。
        这些问题应该能帮助判断用户是初级、中级还是高级水平，以及确定适合的学习目标。
        问题应该是开放式的，能够通过用户的回答了解他们的经验、知识深度和学习意图。
        只返回问题列表，每个问题一行，不要添加其他内容。
        """
        
        try:
            response = self._call_llm(prompt)
            questions = [q.strip() for q in response.strip().split('\n') if q.strip()]
            # 确保至少有5个问题
            while len(questions) < 5:
                questions.append(f"请描述您在{skill_name}方面的一个学习目标或挑战？")
            return questions[:5]  # 只取前5个问题
        except Exception as e:
            print(f"生成评估问题时出错: {e}")
            # 返回默认问题
            return [
                f"您在{skill_name}方面有多少经验？",
                f"您能描述一下您在{skill_name}方面已经掌握的知识点吗？",
                f"您学习{skill_name}的主要目的是什么？",
                f"您曾经完成过{skill_name}相关的项目或作品吗？",
                f"在{skill_name}领域，您觉得最具挑战性的部分是什么？"
            ]
    
    def _analyze_user_responses(self, skill_name: str, user_responses: List[Dict[str, str]]) -> Dict[str, Any]:
        """分析用户回答，确定水平和学习目标"""
        # 构造完整对话内容供LLM分析
        conversation = "\n".join([f"问题: {r['question']}\n回答: {r['answer']}" for r in user_responses])
        
        prompt = f"""
        你是一位教育评估专家。基于以下用户在"{skill_name}"领域的问答内容，请评估用户的水平和学习需求。

        {conversation}

        请提供以下格式的评估结果:
        - 评估的水平: [初级/中级/高级]
        - 水平说明: [简要解释为什么用户属于这个水平]
        - 学习目标: [列出5个针对该用户水平和兴趣的具体学习目标]
        - 建议学习路径: [简要描述适合该用户的学习路径]

        请以JSON格式返回结果，键名为level(beginner/intermediate/advanced), explanation, objectives(数组), learning_path。
        """
        
        try:
            response = self._call_llm(prompt)
            # 尝试解析JSON响应
            try:
                result = json.loads(response)
            except json.JSONDecodeError:
                # 如果响应不是有效JSON，尝试手动解析
                result = self._parse_non_json_response(response)
            
            # 确保结果包含所有必要字段
            if 'level' not in result:
                result['level'] = 'beginner'
            if 'objectives' not in result or not result['objectives']:
                result['objectives'] = [f"学习{skill_name}的基础知识"] * 5
            if len(result['objectives']) < 5:
                result['objectives'].extend([f"深入学习{skill_name}的进阶技能"] * (5 - len(result['objectives'])))
            
            return result
        except Exception as e:
            print(f"分析用户回答时出错: {e}")
            # 返回默认评估结果
            return {
                "level": "beginner",
                "explanation": f"基于默认评估，假定用户在{skill_name}领域为初学者水平。",
                "objectives": [
                    f"掌握{skill_name}的基础概念和术语",
                    f"完成{skill_name}的入门级练习和项目",
                    f"理解{skill_name}的核心原理",
                    f"能够应用{skill_name}解决简单问题",
                    f"建立{skill_name}的学习习惯和方法"
                ],
                "learning_path": f"从基础概念开始，通过实践项目逐步掌握{skill_name}技能。"
            }
    
    def _parse_non_json_response(self, text: str) -> Dict[str, Any]:
        """解析非JSON格式的LLM响应"""
        result = {
            "level": "beginner",
            "explanation": "",
            "objectives": [],
            "learning_path": ""
        }
        
        lines = text.strip().split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if "水平" in line or "level" in line.lower():
                if "初级" in line or "beginner" in line.lower():
                    result["level"] = "beginner"
                elif "中级" in line or "intermediate" in line.lower():
                    result["level"] = "intermediate"
                elif "高级" in line or "advanced" in line.lower():
                    result["level"] = "advanced"
                current_section = "explanation"
            elif "说明" in line or "解释" in line or "explanation" in line.lower():
                current_section = "explanation"
                content = line.split(":", 1)[1].strip() if ":" in line else ""
                if content:
                    result["explanation"] = content
            elif "目标" in line or "objectives" in line.lower():
                current_section = "objectives"
            elif "学习路径" in line or "learning_path" in line.lower():
                current_section = "learning_path"
                content = line.split(":", 1)[1].strip() if ":" in line else ""
                if content:
                    result["learning_path"] = content
            elif current_section == "objectives" and (line.startswith("-") or line.startswith("*") or line[0].isdigit()):
                objective = line.lstrip("- *0123456789. ")
                if objective:
                    result["objectives"].append(objective)
            elif current_section == "explanation" and not result["explanation"]:
                result["explanation"] = line
            elif current_section == "learning_path" and not result["learning_path"]:
                result["learning_path"] = line
        
        return result
    
    def _call_llm(self, prompt: str) -> str:
        """调用LLM API获取响应"""
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位专业的教育评估和课程设计专家，擅长分析学习者需求并制定个性化学习计划。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM API调用失败: {e}")
            raise
    
    def create_user_profile(self, nickname: str, skill_name: str, assessment: Dict[str, Any]) -> UserProfile:
        """创建用户画像"""
        skill = Skill(name=skill_name, level=assessment["level"])
        learning_objectives = assessment["objectives"]
        
        user_profile = UserProfile(
            name=nickname,
            skills=[skill],
            learning_objectives=learning_objectives
        )
        
        # 如果UserProfile支持更多字段，可以增加额外信息
        if hasattr(user_profile, 'set_additional_info'):
            additional_info = {
                "skill_explanation": assessment.get("explanation", ""),
                "recommended_learning_path": assessment.get("learning_path", "")
            }
            user_profile.set_additional_info(additional_info)
        
        return user_profile
