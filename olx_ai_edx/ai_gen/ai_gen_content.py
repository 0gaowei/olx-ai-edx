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

    def __init__(self, max_iterations: int = 1, api_key: str = None, model: str = "deepseek-chat"):
        """初始化AI生成器

        Args:
            max_iterations: 最大迭代次数
            api_key: OpenAI API Key
            model: 选择使用的AI模型
        """
        self.max_iterations = max_iterations
        self.model = model
        if api_key is None:
            api_key = os.getenv("DEEPSEEK_API_KEY")
        
        if model is None:
            BASE_URL = "https://api.deepseek.com"
        elif model.lower() == "glm-4-long":
            BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"

        self.client = OpenAI(api_key=api_key, base_url=BASE_URL)
        # 初始化对话历史
        self.history = []

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
        self.messages = [{
            "role": "user", 
            "content": f"你是一个专业课程设计师。请为用户{user_profile.name}（技能水平：{user_profile.skill_level}）设计一个关于{skill.name}的课程大纲。\n\n"
                       f"用户的学习目标是：{', '.join(user_profile.learning_goals)}\n\n"
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
