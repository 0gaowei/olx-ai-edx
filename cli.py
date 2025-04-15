"""
OLX Course Generator
===============

OLX格式自动课程生成系统 - 基于AI的个性化学习内容生成
"""

from olx_ai_edx.models import UserProfile, Skill
from olx_ai_edx.ai_gen import AIGenerator, CourseGenerationManager
from olx_ai_edx.export import OLXExporter
from olx_ai_edx.ai_gen import UserInteractionManager
import os
from dotenv import load_dotenv

# 加载环境变量，参考文件位于 olx-ai-edx/olx_ai_edx/ref/.env
load_dotenv(os.path.join(os.path.dirname(__file__), 'olx_ai_edx', 'ref', '.env'))


def main():
    """主函数，演示课程生成系统"""

    # 允许用户选择模型
    print("欢迎使用自动课程生成系统！")
    print("\n请选择要使用的模型:")
    print("1. DeepSeek Chat (默认)")
    print("2. GLM-4-Long")
    
    model_choice = input("请输入选项 (1-2): ")
    model = "deepseek-chat"
    if model_choice == "2":
        model = "glm-4-long"
        # 从环境变量中获取API密钥
        api_key = os.getenv("GLM_API_KEY")
    else:
        model = "deepseek-chat"  # 默认模型
        api_key = os.getenv("DEEPSEEK_API_KEY")
    ai_generator = AIGenerator(api_key=api_key, model=model)
    interaction_manager = UserInteractionManager(max_iterations=1, aigenerator=ai_generator)

    # 步骤1：获取用户信息
    nickname, skill_name = interaction_manager.collect_basic_info()

    # 评估用户水平和学习目标
    assessment = interaction_manager.assess_user_level(skill_name)
    learning_path = assessment.get("learning_path", "")


    # 显示评估结果
    print(f"\n您好，{nickname}！")
    print(f"根据评估，您在{skill_name}方面的水平为：{assessment['level']}")
    print(f"水平说明：{assessment.get('explanation', '')}")
    print("\n您的学习目标：")
    for i, objective in enumerate(assessment["objectives"], 1):
        print(f"{i}. {objective}")
    print(f"\n推荐{skill_name}的学习路径：{learning_path}")

    skill = Skill(skill_name, f"{learning_path}")
    
    # 创建用户配置文件和技能
    user = interaction_manager.create_user_profile(nickname, assessment["level"], skill_name=skill_name, learning_goals=skill)

    # 步骤2：生成课程
    course_manager = CourseGenerationManager(max_iterations=1, user_profile=user, skill=skill, aigenerator=ai_generator)
    course = course_manager.generate_course()

    # 步骤3：导出为OLX
    exporter = OLXExporter(course, output_dir=f"output/{course.course}")
    tar_path = exporter.export_to_tar_gz()

    print(f"\n恭喜！您的课程已生成并导出到：{tar_path}")
    print("您可以将此文件导入到 Open edX 平台进行学习。")


if __name__ == '__main__':
    main()
