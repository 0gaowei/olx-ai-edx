# OLX AI Course Generator

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

OLX格式自动课程生成系统 - 基于AI的个性化学习内容生成工具，可将生成的课程直接导入Open edX平台。

## 主要功能

- 基于用户技能水平和学习目标生成个性化课程
- 支持多种AI模型(DeepSeek Chat/GLM-4-Long)
- 交互式命令行界面
- 自动评估用户技能水平
- 生成符合OLX标准的课程包(.tar.gz)
- 支持课程章节、单元、HTML内容、测验问题等多种组件

## 安装指南

1. 确保已安装Python 3.8+
2. 克隆本仓库:

   ```bash
   git clone https://github.com/0gaowei/olx-ai-edx.git
   cd olx-ai-edx
   ```

3. 安装依赖:

   ```bash
   pip install python-dotenv
   ```

## 配置说明

1. 在`olx_ai_edx/ref/.env`文件中配置API密钥:

   ```bash
   GLM_API_KEY=your_api_key_here
   ```

2. 支持的AI模型:
   - deepseek-chat (默认)
   - glm-4-long

## 使用示例

1. 运行交互式命令行界面:

   ```bash
   python cli.py
   ```

2. 按照提示输入:
   - 您的姓名
   - 想学习的技能
   - 回答技能评估问题
   - 输入学习目标

3. 系统将生成课程并导出为.tar.gz文件

## 输出格式

生成的课程包结构:

```bash
output/
  ├── course_name_run1/
  │   ├── course.xml
  │   ├── chapter/
  │   ├── sequential/
  │   ├── vertical/
  │   ├── html/
  │   └── problem/
  └── course_name_run1.tar.gz
```

## 项目结构

```bash
olx-ai-edx/
  ├── olx_ai_edx/          # 核心代码
  │   ├── ai_gen/          # AI生成模块
  │   ├── export/          # OLX导出模块
  │   ├── models/          # 数据模型
  │   └── ref/             # 参考文件
  ├── output/              # 生成的课程
  ├── ai-olx.py            # 完整实现
  ├── cli.py               # 命令行界面
  └── README.md            # 本文件
```

## 许可证

MIT License
