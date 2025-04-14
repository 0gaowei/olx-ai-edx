"""
OLX Course Generator
===============

OLX格式自动课程生成系统 - 基于AI的个性化学习内容生成
"""

from olx_ai_edx.models import UserProfile, Skill
from olx_ai_edx.ai_gen import AIGenerator, CourseGenerationManager
from olx_ai_edx.export import OLXExporter
import os
from dotenv import load_dotenv

# 加载环境变量，参考文件位于 olx-ai-edx/olx_ai_edx/ref/.env
load_dotenv(os.path.join(os.path.dirname(__file__), 'olx_ai_edx', 'ref', '.env'))


def main():
    """主函数，演示课程生成系统"""
    # 步骤1：获取用户输入
    print("欢迎使用自动课程生成系统！")
    name = input("请输入您的姓名: ")
    skill_name = input("请输入您想学习的技能 (如 'Python 编程'): ")

    # 从环境变量中获取API密钥
    api_key = os.getenv("GLM_API_KEY")

    # 允许用户选择模型
    print("\n请选择要使用的模型:")
    print("1. DeepSeek Chat (默认)")
    print("2. GLM-4-Long")
    
    model_choice = input("请输入选项 (1-3): ")
    model = "deepseek-chat"
    
    if model_choice == "2":
        model = "glm-4-long"
    else:
        model = "deepseek-chat"  # 默认模型

    # 创建用户配置文件和技能
    user = UserProfile(name)

    # 模拟技能评估
    print("\n请回答以下问题来评估您的技能水平 (回答 y/n):")
    answers = {}
    answers["q1"] = input("问题1: 您是否了解编程基础概念? (y/n) ").lower() == 'y'
    answers["q2"] = input("问题2: 您是否使用过类似的编程语言? (y/n) ").lower() == 'y'
    answers["q3"] = input("问题3: 您是否完成过相关项目? (y/n) ").lower() == 'y'

    skill_level = user.assess_skill_level(answers)
    print(f"根据您的回答，系统评估您的技能水平为: {skill_level}")

    # 获取学习目标
    print("\n请输入您的学习目标 (输入空行结束):")
    while True:
        goal = input("- 学习目标: ")
        if not goal:
            break
        user.add_learning_goal(goal)

    skill = Skill(skill_name, f"{skill_name}基础知识")

    # 步骤2：生成课程
    ai_generator = AIGenerator(max_iterations=1, api_key=api_key, model=model)  # 演示用限制迭代次数
    manager = CourseGenerationManager(max_iterations=1, user_profile=user, skill=skill, aigenerator=ai_generator)
    course = manager.generate_course()

    # 步骤3：导出为OLX
    exporter = OLXExporter(course, output_dir=f"output/{course.course}")
    tar_path = exporter.export_to_tar_gz()

    print(f"\n恭喜！您的课程已生成并导出到：{tar_path}")
    print("您可以将此文件导入到 Open edX 平台进行学习。")


if __name__ == '__main__':
    main()
