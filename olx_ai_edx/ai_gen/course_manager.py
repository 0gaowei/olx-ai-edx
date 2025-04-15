"""课程生成管理器 - 协调用户配置文件和AI生成过程"""

from typing import Optional

from ..models import UserProfile
from ..models import Skill
from ..models import Course
from .ai_gen_content import AIGenerator
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'ref', '.env'))

class CourseGenerationManager:
    """管理课程生成过程，协调用户配置文件和AI生成"""

    def __init__(self, user_profile: UserProfile, max_iterations: int = 1, skill: Skill = None, aigenerator: Optional[AIGenerator] = None):
        """初始化管理器

        Args:
            user_profile: 用户配置文件
            skill: 技能对象
            aigenerator: AI生成器实例（可选）
        """
        self.user_profile = user_profile
        self.skill = skill
        self.aigenerator = aigenerator
        self.max_iterations = max_iterations

    def generate_course(self) -> Course:
        """协调多轮对话生成课程

        Returns:
            生成的课程对象
        """
        print(f"开始为{self.user_profile.name}生成{self.skill.name}课程...")

        # 阶段1：生成课程大纲
        print("第1阶段：生成课程大纲")
        outline = self.aigenerator.generate_initial_outline(self.user_profile, self.skill)
        print(f"大纲生成完成，共{len(outline['chapters'])}个章节\n{outline}")

        # 阶段1.5：大纲迭代
        for i in range(self.max_iterations):
            review = self.aigenerator.review_outline(outline)
            print(f"大纲评审 #{i + 1}: {review}")
            outline = self.aigenerator.update_outline(outline, review)
            print(f"大纲已更新，现在有{len(outline['chapters'])}个章节\n{outline}")

        # 阶段2：生成章节内容
        print("\n第2阶段：逐章生成内容")
        for i, chapter in enumerate(outline["chapters"]):
            print(f"生成章节 {i + 1}/{len(outline['chapters'])}: {chapter['title']}")

            # 生成章节内容
            chapter_content = self.aigenerator.generate_chapter_content(
                chapter["title"],
                chapter["description"],
                self.user_profile
            )

            # 章节内容迭代
            for j in range(self.max_iterations - 1):  # 章节迭代次数减一
                review = self.aigenerator.review_chapter_content(chapter_content)
                print(f"章节评审 #{j + 1}: {review}")

                if "良好" in review and "完成" in review:
                    print("章节内容已完成")
                    break

                chapter_content = self.aigenerator.update_chapter_content(chapter_content, review)
                print(f"章节内容已更新，现在有{len(chapter_content['components'])}个组件\n{chapter_content}")

            # 用详细内容更新大纲中的章节
            outline["chapters"][i] = chapter_content

        '''
        # 阶段3：整体审校
        print("\n第3阶段：整体审校")
        for i in range(self.max_iterations - 1):  # 最终评审迭代次数减一
            review = self.aigenerator.review_full_course(outline)
            print(f"整体评审 #{i + 1}: {review}")

            if "良好" in review and "完成" in review:
                print("课程已完成")
                break

            outline = self.aigenerator.update_full_course(outline, review)
            print("课程已更新")
        '''

        # 从最终大纲创建Course对象
        course = Course.from_dict(outline)
        print(f"课程生成完成：{course.title}，共{len(course.chapters)}章")


        return course
