"""技能相关模型"""


class Skill:
    """表示用户想要学习的技能"""

    def __init__(self, name: str, description: str):
        """初始化技能

        Args:
            name: 技能名称
            description: 技能描述
        """
        self.name = name
        self.description = description

    def __str__(self) -> str:
        return f"Skill(name={self.name}, description={self.description})"
