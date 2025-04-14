import json
import os
import tarfile
import uuid
from typing import List, Dict, Any, Optional
import shutil


class UserProfile:
    """表示用户的个人资料，其中包含个人信息、技能水平和学习目标。"""

    def __init__(self, name: str, skill_level: Optional[str] = None, learning_goals: Optional[List[str]] = None):
        """使用可选的技能级别和学习目标初始化用户配置文件。"""
        self.name = name
        self.skill_level = skill_level
        self.learning_goals = learning_goals or []

    def assess_skill_level(self, answers: Dict[str, bool]) -> str:
        """根据评估问题的答案评估用户的技能水平。"""
        correct_count = sum(answers.values())

        if correct_count <= 3:
            self.skill_level = "初级"
        elif correct_count <= 7:
            self.skill_level = "中级"
        else:
            self.skill_level = "高级"

        return self.skill_level

    def add_learning_goal(self, goal: str) -> None:
        """将单个学习目标添加到learning_goals列表。"""
        if goal not in self.learning_goals:
            self.learning_goals.append(goal)

    def __str__(self) -> str:
        return f"UserProfile(name={self.name}, skill_level={self.skill_level}, goals={self.learning_goals})"


class Skill:
    """表示用户想要学习的技能。"""

    def __init__(self, name: str, description: str):
        """Initialize a skill with name and description."""
        self.name = name
        self.description = description

    def __str__(self) -> str:
        return f"Skill(name={self.name}, description={self.description})"


class Component:
    """课程组件（HTML、Problem 等）的基类。"""

    def __init__(self, component_type: str):
        """使用组件类型初始化。"""
        self.component_type = component_type
        self.url_name = str(uuid.uuid4())

    def to_olx(self) -> Dict[str, str]:
        """将组件转换为 OLX 格式。"""
        raise NotImplementedError("Subclasses must implement to_olx method")


class HTMLComponent(Component):
    """表示 HTML 内容组件。"""

    def __init__(self, content: str):
        """使用内容初始化 HTML 组件。"""
        super().__init__("html")
        self.content = content

    def to_olx(self) -> Dict[str, str]:
        """Convert HTML component to OLX format."""
        html_path = f"html/{self.url_name}.html"
        html_content = f"""
                        <html>
                        <p>{self.content}</p>
                        </html>
                        """
        xml_path = f"html/{self.url_name}.xml"
        xml_content = f"""
                        <html url_name="{self.url_name}" />
                        """
        return {html_path: html_content, xml_path: xml_content}


class ProblemComponent(Component):
    """表示测验问题组件。"""

    def __init__(self, problem_xml: str):
        """使用问题 XML 初始化 Problem 组件。"""
        super().__init__("problem")
        self.problem_xml = problem_xml

    def to_olx(self) -> Dict[str, str]:
        """将 Problem 组件转换为 OLX 格式。"""
        problem_path = f"problem/{self.url_name}.xml"
        problem_content = self.problem_xml
        return {problem_path: problem_content}


class Vertical:
    """表示 sequential 中包含组件的垂直单元。"""

    def __init__(self, display_name: str, components: List[Component]):
        """使用 name 和 components 初始化 vertical。"""
        self.display_name = display_name
        self.components = components
        self.url_name = str(uuid.uuid4())

    def to_olx(self) -> Dict[str, str]:
        """将垂直格式转换为 OLX 格式。"""
        result = {}

        # 创建垂直 XML
        vertical_path = f"vertical/{self.url_name}.xml"
        vertical_content = f"""
                            <vertical display_name="{self.display_name}">
                            """

        # 将组件添加到垂直
        for component in self.components:
            component_olx = component.to_olx()
            result.update(component_olx)
            vertical_content += f'  <{component.component_type} url_name="{component.url_name}" />\n'

        vertical_content += "</vertical>"
        result[vertical_path] = vertical_content

        return result


class Sequential:
    """表示章节中的顺序单元，包含垂直。"""

    def __init__(self, display_name: str, verticals: List[Vertical]):
        """使用 name 和 verticals 初始化 sequential。"""
        self.display_name = display_name
        self.verticals = verticals
        self.url_name = str(uuid.uuid4())

    def to_olx(self) -> Dict[str, str]:
        """将 sequential 转换为 OLX 格式。"""
        result = {}

        # 创建顺序 XML
        sequential_path = f"sequential/{self.url_name}.xml"
        sequential_content = f"""
<sequential display_name="{self.display_name}">
"""

        # 将垂直添加到顺序
        for vertical in self.verticals:
            vertical_olx = vertical.to_olx()
            result.update(vertical_olx)
            sequential_content += f'  <vertical url_name="{vertical.url_name}" />\n'

        sequential_content += "</sequential>"
        result[sequential_path] = sequential_content

        return result


class Chapter:
    """Represents a chapter in the course, containing sequentials."""

    def __init__(self, display_name: str, sequentials: List[Sequential]):
        """Initialize chapter with name and sequentials."""
        self.display_name = display_name
        self.sequentials = sequentials
        self.url_name = str(uuid.uuid4())

    def to_olx(self) -> Dict[str, str]:
        """Convert chapter to OLX format."""
        result = {}

        # Create chapter XML
        chapter_path = f"chapter/{self.url_name}.xml"
        chapter_content = f"""
<chapter display_name="{self.display_name}">
"""

        # Add sequentials to chapter
        for sequential in self.sequentials:
            sequential_olx = sequential.to_olx()
            result.update(sequential_olx)
            chapter_content += f'  <sequential url_name="{sequential.url_name}" />\n'

        chapter_content += "</chapter>"
        result[chapter_path] = chapter_content

        return result


class Course:
    """Represents a generated course with title and chapters."""

    def __init__(self, title: str):
        """Initialize course with title and empty chapters list."""
        self.title = title
        self.chapters = []
        self.org = "DefaultOrg"
        self.course = title.replace(" ", "_").lower()
        self.run = "run1"
        self.url_name = str(uuid.uuid4())

    def add_chapter(self, chapter: Chapter) -> None:
        """Add a Chapter object to the chapters list."""
        self.chapters.append(chapter)

    @classmethod
    def from_dict(cls, course_dict: Dict[str, Any]) -> 'Course':
        """Create a Course object from a dictionary (AI-generated JSON)."""
        course = cls(course_dict["course_title"])

        for chapter_data in course_dict["chapters"]:
            # Check if this chapter has detailed content
            if "sequentials" in chapter_data:
                sequentials = []
                for sequential_data in chapter_data["sequentials"]:
                    verticals = []
                    for vertical_data in sequential_data.get("verticals", []):
                        components = []

                        # Add HTML component if present
                        if "html" in vertical_data:
                            components.append(HTMLComponent(vertical_data["html"]))

                        # Add Problem component if present
                        if "problem" in vertical_data:
                            components.append(ProblemComponent(vertical_data["problem"]))

                        verticals.append(Vertical(sequential_data.get("title", "Untitled Vertical"), components))

                    sequentials.append(Sequential(sequential_data.get("title", "Untitled Sequential"), verticals))

                course.add_chapter(
                    Chapter(chapter_data.get("title", chapter_data.get("chapter_title", "Untitled Chapter")),
                            sequentials))
            else:
                # Create empty chapter (will be filled later)
                course.add_chapter(Chapter(chapter_data["title"], []))

        return course

    def to_olx(self) -> Dict[str, str]:
        """将课程转换为OLX格式。"""
        result = {}

        # 创建course.xml
        course_xml = f"""
    <course url_name="{self.url_name}" org="{self.org}" course="{self.course}" name="{self.title}"/>
    """
        result["course.xml"] = course_xml

        # 创建policy文件 - 修正路径
        # 注意：policy目录名称必须匹配course.xml中的url_name属性值
        policy_dir = f"policy/{self.url_name}"  # 修正的路径结构

        # 增加更多policy参数
        policy_content = {
            "course/{}".format(self.url_name): {
                "display_name": self.title,
                "start": "2023-09-01T00:00:00Z",  # 添加课程开始日期
                "end": "2023-12-31T23:59:59Z",  # 添加课程结束日期
                "show_calculator": True,
                "show_reset_button": True,
                "tabs": [
                    {
                        "course_staff_only": False,
                        "name": "课程",
                        "type": "course_info"
                    },
                    {
                        "course_staff_only": False,
                        "name": "讨论",
                        "type": "discussion"
                    },
                    {
                        "course_staff_only": False,
                        "name": "进度",
                        "type": "progress"
                    }
                ],
                "discussion_topics": {
                    "总讨论区": {
                        "id": "course"
                    }
                }
            }
        }
        result[f"{policy_dir}/policy.json"] = json.dumps(policy_content, indent=2)

        # 创建course文件夹内容
        course_path = f"course/{self.url_name}.xml"
        course_content = f"""
    <course display_name="{self.title}" language="zh">
    """

        # 添加章节到课程
        for chapter in self.chapters:
            chapter_olx = chapter.to_olx()
            result.update(chapter_olx)
            course_content += f'  <chapter url_name="{chapter.url_name}" />\n'

        course_content += "</course>"
        result[course_path] = course_content

        return result


class AIGenerator:
    """Simulates an AI model generating course content through multi-round dialogue."""

    def __init__(self, max_iterations: int = 3):
        """Initialize AI generator with maximum iterations."""
        self.max_iterations = max_iterations

    def generate_initial_outline(self, user_profile: UserProfile, skill: Skill) -> Dict[str, Any]:
        """Generate initial course outline based on user profile and skill.

        In a real system, this would call the AI API with an appropriate prompt.
        For demonstration, we return a sample outline.
        """
        # This would be replaced with actual AI API calls in a real system
        return {
            "course_title": f"{skill.name} course of {user_profile.name}",
            "chapters": [
                {"title": f"Chapter 1: {skill.name}简介", "description": f"了解{skill.name}的历史和用途"},
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
        """Review course outline, providing feedback.

        In a real system, this would call the AI API with an appropriate prompt.
        """
        # This would be replaced with actual AI API calls
        return "大纲总体不错，但可以考虑增加更多实践内容，特别是在前面的章节中。"

    def update_outline(self, outline: Dict[str, Any], review: str) -> Dict[str, Any]:
        """Update outline based on review.

        In a real system, this would call the AI API with the current outline and review.
        """
        # In a real system, this would use AI to update the outline
        # For demo purposes, we'll manually modify it
        updated_outline = outline.copy()
        # Add practical examples to each chapter description
        for chapter in updated_outline["chapters"]:
            chapter["description"] += "，包含实践练习"

        return updated_outline

    def generate_chapter_content(self, chapter_title: str, chapter_description: str, user_profile: UserProfile) -> \
            Dict[str, Any]:
        """Generate content for a specific chapter.

        In a real system, this would call the AI API with chapter info and user profile.
        """
        # This would be replaced with actual AI API calls
        return {
            "chapter_title": chapter_title,
            "sequentials": [
                {
                    "title": f"Unit 1: {chapter_title}理论基础",
                    "verticals": [
                        {
                            "html": f"<p>这是{chapter_title}的基础理论内容。</p>"
                                    f"<p>适合{user_profile.skill_level}水平的学习者。</p>",
                            "problem": f"<problem>"
                                       f"<p>关于{chapter_title}的测验问题</p>"
                                       f"<choiceresponse>"
                                       f"<choice correct='true'>正确选项</choice>"
                                       f"<choice correct='false'>错误选项</choice>"
                                       f"</choiceresponse>"
                                       f"</problem>"
                        }
                    ]
                },
                {
                    "title": f"Unit 2: {chapter_title}实践应用",
                    "verticals": [
                        {
                            "html": f"<p>这是{chapter_title}的实践应用内容。</p>"
                                    f"<p>包含代码示例和实践任务。</p>",
                            "problem": f"<problem>"
                                       f"<p>完成以下代码来实现{chapter_title}的功能：</p>"
                                       f"<coderesponse>"
                                       f"<textbox mode='python'/>"
                                       f"</coderesponse>"
                                       f"</problem>"
                        }
                    ]
                }
            ]
        }

    def review_chapter_content(self, chapter_content: Dict[str, Any]) -> str:
        """Review chapter content, providing feedback.

        In a real system, this would call the AI API with the chapter content.
        """
        # This would be replaced with actual AI API calls
        return "章节内容可以增加更多实际代码示例，帮助学习者理解概念。"

    def update_chapter_content(self, chapter_content: Dict[str, Any], review: str) -> Dict[str, Any]:
        """Update chapter content based on review.

        In a real system, this would call the AI API with current content and review.
        """
        # In a real system, this would use AI to update the content
        # For demo purposes, we'll manually modify it
        updated_content = chapter_content.copy()

        # Add code examples to HTML content
        for sequential in updated_content["sequentials"]:
            for vertical in sequential["verticals"]:
                if "html" in vertical:
                    vertical["html"] += "<pre><code>print('Hello, World!')</code></pre>"

        return updated_content

    def review_full_course(self, course_dict: Dict[str, Any]) -> str:
        """Review the entire course, checking for consistency and completeness.

        In a real system, this would call the AI API with the full course.
        """
        # This would be replaced with actual AI API calls
        return "课程整体结构良好，但应确保章节之间有清晰的衔接，并检查专业术语使用是否一致。"

    def update_full_course(self, course_dict: Dict[str, Any], review: str) -> Dict[str, Any]:
        """Update the entire course based on review.

        In a real system, this would call the AI API with the current course and review.
        """
        # In a real system, this would use AI to update the course
        # For demo purposes, we'll return the course with minor modifications
        updated_course = course_dict.copy()

        # Add a note about terminology consistency to each chapter
        for chapter in updated_course["chapters"]:
            if "sequentials" in chapter:
                for sequential in chapter["sequentials"]:
                    for vertical in sequential["verticals"]:
                        if "html" in vertical:
                            vertical["html"] += "<p><strong>注意：</strong>本章使用的专业术语与其他章节保持一致。</p>"

        return updated_course


class CourseGenerationManager:
    """Manages the course generation process, coordinating user profile and AI generation."""

    def __init__(self, user_profile: UserProfile, skill: Skill, aigenerator: AIGenerator = None,
                 max_iterations: int = 3):
        """Initialize manager with user profile, skill, and AI generator."""
        self.user_profile = user_profile
        self.skill = skill
        self.aigenerator = aigenerator or AIGenerator(max_iterations)
        self.max_iterations = max_iterations

    def generate_course(self) -> Course:
        """Coordinate multi-round dialogue to generate a course."""
        print(f"开始为{self.user_profile.name}生成{self.skill.name}课程...")

        # Stage 1: Generate course outline
        print("第1阶段：生成课程大纲")
        outline = self.aigenerator.generate_initial_outline(self.user_profile, self.skill)

        for i in range(self.max_iterations):
            review = self.aigenerator.review_outline(outline)
            print(f"大纲评审 #{i + 1}: {review}")

            if "不错" in review and "完成" in review:
                print("大纲已完成，进入下一阶段")
                break

            outline = self.aigenerator.update_outline(outline, review)
            print(f"大纲已更新，现在有{len(outline['chapters'])}个章节")

        # Stage 2: Generate chapter content
        print("\n第2阶段：逐章生成内容")
        for i, chapter in enumerate(outline["chapters"]):
            print(f"生成章节 {i + 1}/{len(outline['chapters'])}: {chapter['title']}")

            chapter_content = self.aigenerator.generate_chapter_content(
                chapter["title"],
                chapter["description"],
                self.user_profile
            )

            for j in range(self.max_iterations - 1):  # One less iteration for chapters
                review = self.aigenerator.review_chapter_content(chapter_content)
                print(f"章节评审 #{j + 1}: {review}")

                if "良好" in review and "完成" in review:
                    print("章节内容已完成")
                    break

                chapter_content = self.aigenerator.update_chapter_content(chapter_content, review)
                print("章节内容已更新")

            # Update the chapter in the outline with detailed content
            outline["chapters"][i] = chapter_content

        # Stage 3: Review full course
        print("\n第3阶段：整体审校")
        for i in range(self.max_iterations - 1):  # One less iteration for final review
            review = self.aigenerator.review_full_course(outline)
            print(f"整体评审 #{i + 1}: {review}")

            if "良好" in review and "完成" in review:
                print("课程已完成")
                break

            outline = self.aigenerator.update_full_course(outline, review)
            print("课程已更新")

        # Create Course object from the final outline
        course = Course.from_dict(outline)
        print(f"课程生成完成：{course.title}，共{len(course.chapters)}章")

        return course


class OLXExporter:
    """Exports a course to OLX format and compresses it as a .tar.gz file."""

    def __init__(self, course: Course, output_dir: str = "output"):
        """Initialize exporter with course and output directory."""
        self.course = course
        self.output_dir = output_dir
        self.course_dir = os.path.join(output_dir, f"{course.course}-{course.run}")

    def export_to_tar_gz(self) -> str:
        """Export course to .tar.gz file."""
        # Create output directory if it doesn't exist
        if os.path.exists(self.course_dir):
            shutil.rmtree(self.course_dir)
        os.makedirs(self.course_dir, exist_ok=True)
        print(f"课程输出目录: {self.course_dir}")

        # Convert course to OLX format
        olx_files = self.course.to_olx()

        # Write OLX files to disk
        for file_path, content in olx_files.items():
            full_path = os.path.join(self.course_dir, file_path)
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

        # Create .tar.gz file
        tar_path = f"{self.course_dir}.tar.gz"
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(self.course_dir, arcname=os.path.basename(self.course_dir))

        print(f"课程已导出到: {tar_path}")
        return tar_path


def main():
    """Main function to demonstrate the course generation system."""
    # Step 1: Get user input
    print("欢迎使用自动课程生成系统！")
    name = input("请输入您的姓名: ")
    skill_name = input("请输入您想学习的技能 (如 'Python 编程'): ")

    # Create user profile and skill
    user = UserProfile(name)

    # Simulate skill assessment with a few questions
    print("\n请回答以下问题来评估您的技能水平 (回答 y/n):")
    answers = {}
    answers["q1"] = input("问题1: 您是否了解编程基础概念? (y/n) ").lower() == 'y'
    answers["q2"] = input("问题2: 您是否使用过类似的编程语言? (y/n) ").lower() == 'y'
    answers["q3"] = input("问题3: 您是否完成过相关项目? (y/n) ").lower() == 'y'

    skill_level = user.assess_skill_level(answers)
    print(f"根据您的回答，系统评估您的技能水平为: {skill_level}")

    # Get learning goals
    print("\n请输入您的学习目标 (输入空行结束):")
    while True:
        goal = input("- 学习目标: ")
        if not goal:
            break
        user.add_learning_goal(goal)

    skill = Skill(skill_name, f"{skill_name}基础知识")

    # Step 2: Generate course
    ai_generator = AIGenerator(max_iterations=2)  # Limit iterations for demo
    manager = CourseGenerationManager(user, skill, ai_generator)
    course = manager.generate_course()

    # Step 3: Export to OLX
    exporter = OLXExporter(course, f"output/{course.course}_{course.run}")
    tar_path = exporter.export_to_tar_gz()

    print(f"\n恭喜！您的课程已生成并导出到：{tar_path}")
    print("您可以将此文件导入到 Open edX 平台进行学习。")


if __name__ == "__main__":
    main()
