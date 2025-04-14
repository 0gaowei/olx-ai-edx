"""OLX导出模块 - 将课程导出为OLX格式"""

import os
import shutil
import tarfile

from models.course import Course


class OLXExporter:
    """将课程导出为OLX格式并压缩为.tar.gz文件"""

    def __init__(self, course: Course, output_dir: str = "output"):
        """初始化导出器

        Args:
            course: 课程对象
            output_dir: 输出目录
        """
        self.course = course
        self.output_dir = output_dir
        self.course_dir = f"{output_dir}/{course.course}_{course.run}"

    def export_to_tar_gz(self) -> str:
        """导出课程为.tar.gz文件

        Returns:
            tar.gz文件路径
        """
        # 如果输出目录已存在则删除
        if os.path.exists(self.course_dir):
            shutil.rmtree(self.course_dir)
        os.makedirs(self.course_dir, exist_ok=True)
        print(f"课程完整路径：{self.course_dir}")

        # 将课程转换为OLX格式
        olx_files = self.course.to_olx()

        # 将OLX文件写入磁盘
        for file_path, content in olx_files.items():
            full_path = os.path.join(self.course_dir, file_path)
            # 创建目录（如果不存在）
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

        # 创建.tar.gz文件
        tar_path = os.path.join(os.path.dirname(self.course_dir), f"{self.course.course}.tar.gz")
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(self.course_dir, arcname="course")

        print(f"课程已导出到: {tar_path}")
        return tar_path
