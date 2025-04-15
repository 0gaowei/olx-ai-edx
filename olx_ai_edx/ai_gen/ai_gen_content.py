"""AI生成器模块 - 模拟AI模型生成课程内容"""

from typing import Dict, Any, List, Union
from openai import OpenAI
import os
from dotenv import load_dotenv

from ..models import UserProfile
from ..models import Skill

import json

# 加载环境变量../ref/.env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'ref', '.env'))

class AIGenerator:
    """模拟AI模型通过多轮对话生成课程内容"""

    def __init__(self, api_key: str = None, model: str = "deepseek-chat"):
        """初始化AI生成器

        Args:
            api_key: OpenAI API Key
            model: 选择使用的AI模型
        """
        self.model = model
        if api_key is None:
            api_key = os.getenv("DEEPSEEK_API_KEY")
        
        if model is None:
            BASE_URL = "https://api.deepseek.com"
        elif model.lower() == "glm-4-long":
            BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"

        self.client = OpenAI(api_key=api_key, base_url=BASE_URL)
        # 初始化对话历史
        self.messages = []

    def _call_llm_api(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """调用大语言模型API
        
        Args:
            messages: 消息历史列表
            
        Returns:
            API响应对象
        """
        if "glm" in self.model.lower():
            # GLM模型的API调用
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
        else:
            # DeepSeek或其他模型的默认API调用
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            
        return response

    def generate_initial_outline(self, user_profile: UserProfile, skill: Skill) -> Dict[str, Any]:
        """根据用户配置文件和技能生成初始课程大纲

        在真实系统中，这会调用AI API附带适当的提示。
        演示用，返回样例大纲。

        Args:
            user_profile: 用户配置文件
            skill: 技能对象

        Returns:
            课程大纲字典
        """
        # 创建提示，开始新的对话
        self.messages=[{
            "role": "user", 
            "content": f"你是一个专业课程设计师。请为用户{user_profile.name}（技能水平：{user_profile.skill_level}）设计一个关于{skill.name}的课程大纲。\n\n"
                       f"用户的学习目标是：{', '.join(user_profile.learning_goals.description)}\n\n"
                       f"请以JSON格式输出，包含course_title和chapters数组，每个chapter包含title和description。"
        }]
        
        # 调用DeepSeek API
        response = self._call_llm_api(self.messages)
        
        # 保存回复到对话历史
        self.messages.append(response.choices[0].message)
        
        # 尝试解析JSON响应
        try:
            # 从回复文本中提取JSON部分
            content = response.choices[0].message.content
            # 查找可能的JSON开始和结束位置
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = content[start:end]
                return json.loads(json_str)
            else:
                # 如果未找到JSON，使用默认结构
                return self._create_default_outline(skill.name, user_profile.name)
        except json.JSONDecodeError:
            # 解析失败时使用默认结构
            return self._create_default_outline(skill.name, user_profile.name)

    def _create_default_outline(self, skill_name, user_name):
        """创建默认大纲结构（当API响应解析失败时使用）"""
        return {
            "course_title": f"{skill_name} course of {user_name}",
            "chapters": [
                {"title": f"Chapter 1: {skill_name}简介", "description": f"了解{skill_name}的历史和用途"},
                {"title": "Chapter 2: 基本语法", "description": "学习基础语法和结构"},
                {"title": "Chapter 3: 数据类型", "description": "熟悉常用数据类型"},
                {"title": "Chapter 4: 控制结构", "description": "学习条件和循环"},
                {"title": "Chapter 5: 函数", "description": "掌握函数定义和使用"},
                {"title": "Chapter 6: 模块和包", "description": "了解模块化编程"},
                {"title": "Chapter 7: 文件操作", "description": "学习文件读写操作"},
                {"title": "Chapter 8: 异常处理", "description": "掌握错误和异常处理"},
                {"title": "Chapter 9: 面向对象编程", "description": "理解面向对象概念"},
                {"title": "Chapter 10: 项目实践", "description": "完成一个简单项目"}
            ]
        }
    
    def review_outline(self, outline: Dict[str, Any]) -> str:
        """评审课程大纲，提供反馈

        Args:
            outline: 课程大纲字典

        Returns:
            评审反馈
        """
        # 将大纲添加到对话历史
        self.messages.append({
            "role": "user",
            "content": f"请评审以下课程大纲，并提供改进建议：\n\n{outline}"
        })

        # 调用DeepSeek API
        response = self._call_llm_api(self.messages)
        
        # 保存回复到对话历史
        self.messages.append(response.choices[0].message)

        # return "大纲总体不错，但可以考虑增加更多实践内容，特别是在前面的章节中。"
        return response.choices[0].message.content
    
    def update_outline(self, outline: Dict[str, Any], review: str) -> Dict[str, Any]:
        """根据评审更新大纲

        Args:
            outline: 当前大纲字典
            review: 评审反馈

        Returns:
            更新后的大纲字典
        """
        # 请求更新大纲
        self.messages.append({
            "role": "user",
            "content": f"根据以下评审反馈，更新课程大纲。请保持JSON格式输出。\n\n评审反馈：{review}\n\n当前大纲：{outline}"
        })
        
        # 调用DeepSeek API
        response = self._call_llm_api(self.messages)
        
        # 保存回复到对话历史
        self.messages.append(response.choices[0].message)
        
        # 尝试解析JSON响应
        try:
            # 从回复文本中提取JSON部分
            content = response.choices[0].message.content
            # 查找可能的JSON开始和结束位置
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = content[start:end]
                return json.loads(json_str)
            else:
                # 解析失败则返回原大纲
                return outline
        except json.JSONDecodeError:
            # 解析失败则返回原大纲
            return outline

    def generate_chapter_content(self, chapter_title: str, chapter_description: str, user_profile: UserProfile) -> Dict[
        str, Any]:
        """生成特定章节的内容

        Args:
            chapter_title: 章节标题
            chapter_description: 章节描述
            user_profile: 用户配置文件

        Returns:
            章节内容字典
        """
        # 请求生成章节内容
        self.messages.append({
            "role": "user",
            "content": f"请为以下章节生成详细内容：\n\n标题：{chapter_title}\n描述：{chapter_description}\n\n"
                       f"内容应适合{user_profile.skill_level}水平的学习者。请以JSON格式输出，包含chapter_title和sequentials数组，"
                       f"每个sequential包含title和verticals数组，每个vertical包含html和problem字段。"
        })
        
        # 调用DeepSeek API
        response = self._call_llm_api(self.messages)
        
        # 保存回复到对话历史
        self.messages.append(response.choices[0].message)
        
        # 尝试解析JSON响应
        try:
            # 从回复文本中提取JSON部分
            content = response.choices[0].message.content
            # 查找可能的JSON开始和结束位置
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = content[start:end]
                return json.loads(json_str)
            else:
                # 解析失败则返回默认章节内容
                return self._create_default_chapter_content(chapter_title, chapter_description, user_profile)
        except json.JSONDecodeError:
            # 解析失败则返回默认章节内容
            return self._create_default_chapter_content(chapter_title, chapter_description, user_profile)

    def _create_default_chapter_content(self, chapter_title, chapter_description, user_profile):
        """创建默认章节内容（当API响应解析失败时使用）"""
        return {
            "chapter_title": chapter_title,
            "sequentials": [
                {
                    "title": f"Unit 1: {chapter_title}理论基础",
                    "verticals": [
                        {
                            "html": f"<p>这是{chapter_title}的基础理论内容。</p><p>适合{user_profile.skill_level}水平的学习者。</p>",
                            "problem": f"<problem><p>关于{chapter_title}的测验问题</p><choiceresponse><choice correct='true'>正确选项</choice><choice correct='false'>错误选项</choice></choiceresponse></problem>"
                        }
                    ]
                },
                {
                    "title": f"Unit 2: {chapter_title}实践应用",
                    "verticals": [
                        {
                            "html": f"<p>这是{chapter_title}的实践应用内容。</p><p>包含代码示例和实践任务。</p>",
                            "problem": f"<problem><p>完成以下代码来实现{chapter_title}的功能：</p><coderesponse><textbox mode='python'/></coderesponse></problem>"
                        }
                    ]
                }
            ]
        }
    
    def review_chapter_content(self, chapter_content: Dict[str, Any]) -> str:
        """评审章节内容，提供反馈

        Args:
            chapter_content: 章节内容字典

        Returns:
            评审反馈
        """
        self.messages.append({
            "role": "user",
            "content": f"请评审以下章节内容，并提供改进建议：\n\n{chapter_content}"
        })
        
        response = self._call_llm_api(self.messages)
        
        self.messages.append(response.choices[0].message)
        return response.choices[0].message.content

    def update_chapter_content(self, chapter_content: Dict[str, Any], review: str) -> Dict[str, Any]:
        """根据评审更新章节内容

        Args:
            chapter_content: 当前章节内容字典
            review: 评审反馈

        Returns:
            更新后的章节内容字典
        """
        self.messages.append({
            "role": "user",
            "content": f"根据以下评审反馈，更新章节内容。请保持JSON格式输出。\n\n评审反馈：{review}\n\n当前内容：{chapter_content}"
        })
        
        response = self._call_llm_api(self.messages)
        
        self.messages.append(response.choices[0].message)
        
        # JSON解析逻辑
        try:
            content = response.choices[0].message.content
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = content[start:end]
                return json.loads(json_str)
            else:
                return chapter_content
        except json.JSONDecodeError:
            return chapter_content

    def review_full_course(self, course_dict: Dict[str, Any]) -> str:
        """评审整个课程，检查一致性和完整性

        Args:
            course_dict: 课程字典

        Returns:
            评审反馈
        """
        self.messages.append({
            "role": "user",
            "content": f"请评审以下完整课程，检查一致性和完整性：\n\n{course_dict}"
        })
        
        response = self._call_llm_api(self.messages)

        self.messages.append(response.choices[0].message)
        return response.choices[0].message.content

    def update_full_course(self, course_dict: Dict[str, Any], review: str) -> Dict[str, Any]:
        """根据评审更新整个课程

        Args:
            course_dict: 当前课程字典
            review: 评审反馈

        Returns:
            更新后的课程字典
        """
        # 类似update_chapter_content的实现
        self.messages.append({
            "role": "user",
            "content": f"根据以下评审反馈，更新完整课程。请保持JSON格式输出。\n\n评审反馈：{review}\n\n当前课程：{course_dict}"
        })
        
        response = self._call_llm_api(self.messages)
        
        self.messages.append(response.choices[0].message)
        
        # JSON解析逻辑
        try:
            content = response.choices[0].message.content
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = content[start:end]
                return json.loads(json_str)
            else:
                return course_dict
        except json.JSONDecodeError:
            return course_dict

    def generate_assessment_questions(self, skill_name: str) -> List[str]:
        """
        生成用于评估用户技能水平的问题
        
        Args:
            skill_name: 要评估的技能名称
            model: 使用的LLM模型名称
            
        Returns:
            包含5个评估问题的列表
        """
        prompt = f"""
        你是一位教育评估专家。请为评估用户在"{skill_name}"领域的水平生成5个有效问题。
        这些问题应该能帮助判断用户是初级、中级还是高级水平，以及确定适合的学习目标。
        问题应该是开放式的，能够通过用户的回答了解他们的经验、知识深度和学习意图。
        只返回问题列表，每个问题一行，不要添加其他内容。
        """
        self.messages.append({
            "role": "user",
            "content": prompt
        })
        
        response = self._call_llm_api(self.messages)
        self.messages.append(response.choices[0].message.content)

        questions = [q.strip() for q in response.choices[0].message.content.strip().split('\n') if q.strip()]
        
        # 确保至少有5个问题
        while len(questions) < 5:
            questions.append(f"请描述您在{skill_name}方面的一个学习目标或挑战？")
        
        return questions[:5]  # 只取前5个问题

    def analyze_user_responses(self, skill_name: str, user_responses: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        分析用户的回答，评估技能水平并生成学习目标
        
        Args:
            skill_name: 技能名称
            user_responses: 用户问答列表，每项包含'question'和'answer'键
            model: 使用的LLM模型名称
            
        Returns:
            包含评估结果的字典，包括level、explanation、objectives和learning_path
        """
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
        self.messages.append({
            "role": "user",
            "content": prompt
        })
        response = self._call_llm_api(self.messages)
        self.messages.append(response.choices[0].message)
        
        # 尝试解析JSON响应
        try:
            content = response.choices[0].message.content
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = content[start:end]
                result = json.loads(json_str)
        except json.JSONDecodeError:
            # 如果响应不是有效JSON，尝试手动解析
            result = self.parse_assessment_response(response, skill_name)
        
        # 确保结果包含所有必要字段并规范化
        if 'level' not in result:
            result['level'] = 'beginner'
        elif result['level'] not in ['beginner', 'intermediate', 'advanced']:
            # 将中文或其他表述转换为标准级别
            level_text = result['level'].lower()
            if '初' in level_text or 'begin' in level_text:
                result['level'] = 'beginner'
            elif '中' in level_text or 'inter' in level_text:
                result['level'] = 'intermediate'
            elif '高' in level_text or 'adv' in level_text:
                result['level'] = 'advanced'
            else:
                result['level'] = 'beginner'
        
        if 'objectives' not in result or not result['objectives']:
            result['objectives'] = [f"学习{skill_name}的基础知识"] * 5
        if len(result['objectives']) < 5:
            result['objectives'].extend([f"深入学习{skill_name}的进阶技能"] * (5 - len(result['objectives'])))
        
        if 'explanation' not in result:
            result['explanation'] = f"根据您的回答，系统评估您在{skill_name}领域的水平为{result['level']}。"
        
        if 'learning_path' not in result:
            result['learning_path'] = f"从基础概念开始，通过实践项目逐步掌握{skill_name}技能。"
        
        return result

    def parse_assessment_response(text: str) -> Dict[str, Any]:
        """
        解析非JSON格式的LLM评估响应
        
        Args:
            text: LLM返回的文本
            skill_name: 技能名称
            
        Returns:
            解析后的评估结果字典
        """
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
