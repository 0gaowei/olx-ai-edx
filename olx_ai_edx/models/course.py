"""课程结构相关模型"""

import json
import uuid
from typing import List, Dict, Any


class Component:
    """课程组件基类 (HTML, Problem 等)"""

    def __init__(self, component_type: str):
        """初始化组件

        Args:
            component_type: 组件类型
        """
        self.component_type = component_type
        self.url_name = str(uuid.uuid4())

    def to_olx(self) -> Dict[str, str]:
        """转换为OLX格式

        Returns:
            OLX文件路径和内容的字典 {路径: 内容}

        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError("子类必须实现to_olx方法")


class HTMLComponent(Component):
    """HTML内容组件"""

    def __init__(self, content: str):
        """初始化HTML组件

        Args:
            content: HTML内容
        """
        super().__init__("html")
        self.content = content

    def to_olx(self) -> Dict[str, str]:
        """转换HTML组件为OLX格式

        Returns:
            OLX文件路径和内容的字典
        """
        html_path = f"html/{self.url_name}.html"
        html_content = f"""
<html>
<p>{self.content}</p>
</html>
"""
        xml_path = f"html/{self.url_name}.xml"
        xml_content = f"""
<html filename="{self.url_name}" />
"""
        return {html_path: html_content, xml_path: xml_content}


class ProblemComponent(Component):
    """测验问题组件"""

    def __init__(self, problem_xml: str):
        """初始化Problem组件

        Args:
            problem_xml: 问题的XML定义
        """
        super().__init__("problem")
        self.problem_xml = problem_xml

    def to_olx(self) -> Dict[str, str]:
        """转换Problem组件为OLX格式

        Returns:
            OLX文件路径和内容的字典
        """
        problem_path = f"problem/{self.url_name}.xml"
        problem_content = self.problem_xml
        return {problem_path: problem_content}


class Vertical:
    """垂直单元，包含组件"""

    def __init__(self, display_name: str, components: List[Component]):
        """初始化垂直单元

        Args:
            display_name: 显示名称
            components: 组件列表
        """
        self.display_name = display_name
        self.components = components
        self.url_name = str(uuid.uuid4())

    def to_olx(self) -> Dict[str, str]:
        """转换垂直单元为OLX格式

        Returns:
            OLX文件路径和内容的字典
        """
        result = {}

        # 创建vertical XML
        vertical_path = f"vertical/{self.url_name}.xml"
        vertical_content = f"""
<vertical display_name="{self.display_name}">
"""

        # 添加组件到vertical
        for component in self.components:
            component_olx = component.to_olx()
            result.update(component_olx)
            vertical_content += f'  <{component.component_type} url_name="{component.url_name}" />\n'

        vertical_content += "</vertical>"
        result[vertical_path] = vertical_content

        return result


class Sequential:
    """顺序单元，包含垂直单元"""

    def __init__(self, display_name: str, verticals: List[Vertical]):
        """初始化顺序单元

        Args:
            display_name: 显示名称
            verticals: 垂直单元列表
        """
        self.display_name = display_name
        self.verticals = verticals
        self.url_name = str(uuid.uuid4())

    def to_olx(self) -> Dict[str, str]:
        """转换顺序单元为OLX格式

        Returns:
            OLX文件路径和内容的字典
        """
        result = {}

        # 创建sequential XML
        sequential_path = f"sequential/{self.url_name}.xml"
        sequential_content = f"""
<sequential display_name="{self.display_name}">
"""

        # 添加verticals到sequential
        for vertical in self.verticals:
            vertical_olx = vertical.to_olx()
            result.update(vertical_olx)
            sequential_content += f'  <vertical url_name="{vertical.url_name}" />\n'

        sequential_content += "</sequential>"
        result[sequential_path] = sequential_content

        return result


class Chapter:
    """章节，包含顺序单元"""

    def __init__(self, display_name: str, sequentials: List[Sequential]):
        """初始化章节

        Args:
            display_name: 显示名称
            sequentials: 顺序单元列表
        """
        self.display_name = display_name
        self.sequentials = sequentials
        self.url_name = str(uuid.uuid4())

    def to_olx(self) -> Dict[str, str]:
        """转换章节为OLX格式

        Returns:
            OLX文件路径和内容的字典
        """
        result = {}

        # 创建chapter XML
        chapter_path = f"chapter/{self.url_name}.xml"
        chapter_content = f"""
<chapter display_name="{self.display_name}">
"""

        # 添加sequentials到chapter
        for sequential in self.sequentials:
            sequential_olx = sequential.to_olx()
            result.update(sequential_olx)
            chapter_content += f'  <sequential url_name="{sequential.url_name}" />\n'

        chapter_content += "</chapter>"
        result[chapter_path] = chapter_content

        return result


class Course:
    """生成的课程，包含标题和章节"""

    def __init__(self, title: str):
        """初始化课程

        Args:
            title: 课程标题
        """
        self.title = title
        self.chapters = []
        self.org = "DefaultOrg"
        self.course = title.replace(" ", "_").lower()
        self.run = "run1"
        # self.url_name = str(uuid.uuid4())
        self.url_name = self.course

    def add_chapter(self, chapter: Chapter) -> None:
        """添加章节

        Args:
            chapter: 章节对象
        """
        self.chapters.append(chapter)

    @classmethod
    def from_dict(cls, course_dict: Dict[str, Any]) -> 'Course':
        """从字典创建课程对象（AI生成的JSON）

        Args:
            course_dict: 课程字典

        Returns:
            Course对象
        """
        course = cls(course_dict["course_title"])

        for chapter_data in course_dict["chapters"]:
            # 检查章节是否有详细内容
            if "sequentials" in chapter_data:
                sequentials = []
                for sequential_data in chapter_data["sequentials"]:
                    verticals = []
                    for vertical_data in sequential_data.get("verticals", []):
                        components = []

                        # 添加HTML组件（如果存在）
                        if "html" in vertical_data:
                            components.append(HTMLComponent(vertical_data["html"]))

                        # 添加Problem组件（如果存在）
                        if "problem" in vertical_data:
                            components.append(ProblemComponent(vertical_data["problem"]))

                        verticals.append(Vertical(sequential_data.get("title", "Untitled Vertical"), components))

                    sequentials.append(Sequential(sequential_data.get("title", "Untitled Sequential"), verticals))

                course.add_chapter(
                    Chapter(chapter_data.get("title", chapter_data.get("chapter_title", "Untitled Chapter")),
                            sequentials))
            else:
                # 创建空章节（稍后填充）
                course.add_chapter(Chapter(chapter_data["title"], []))

        return course

    def to_olx(self) -> Dict[str, str]:
        """转换课程为OLX格式

        Returns:
            OLX文件路径和内容的字典
        """
        result = {}

        # 创建course.xml
        course_xml = f"""
<course url_name="{self.course}" org="{self.org}" course="{self.run}"/>
"""
        result["course.xml"] = course_xml

        # 创建policy文件
        policy_dir = f"policies/{self.url_name}"
        policy_content = {
            "course/{}".format(self.url_name): {
                "display_name": self.title
            }
        }
        result[f"{policy_dir}/policy.json"] = json.dumps(policy_content, indent=2)

        # 创建course文件夹内容
        course_path = f"course/{self.url_name}.xml"
        course_content = f"""
<course display_name="{self.title}" language="en">
"""

        # 添加chapters到course
        for chapter in self.chapters:
            chapter_olx = chapter.to_olx()
            result.update(chapter_olx)
            course_content += f'  <chapter url_name="{chapter.url_name}" />\n'

        course_content += "</course>"
        result[course_path] = course_content

        return result
