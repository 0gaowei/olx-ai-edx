from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
import uuid
from dotenv import load_dotenv

from olx_ai_edx.models import UserProfile, Skill
from olx_ai_edx.ai_gen import AIGenerator, CourseGenerationManager
from olx_ai_edx.export import OLXExporter

# 加载环境变量
load_dotenv(os.path.join(os.path.dirname(__file__), 'olx_ai_edx', 'ref', '.env'))

app = Flask(__name__)
# CORS(app)  # 允许跨域请求
CORS(app, resources={r"/api/*": {"origins": "http://127.0.0.1:5500"}})

# 存储用户会话状态
sessions = {}


@app.route('/api/start_session', methods=['POST'])
def start_session():
    """开始新的会话"""
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        'state': 'welcome',
        'data': {}
    }
    return jsonify({
        'session_id': session_id,
        'message': '欢迎使用自动课程生成系统！',
        'next_prompt': '请输入您的姓名:'
    })


@app.route('/api/interact', methods=['POST'])
def interact():
    """处理用户输入"""
    data = request.json
    session_id = data.get('session_id')
    user_input = data.get('user_input')

    if session_id not in sessions:
        return jsonify({'error': '会话不存在或已过期'}), 400

    session = sessions[session_id]
    state = session['state']

    # 处理不同状态下的用户输入
    if state == 'welcome':
        # 处理用户姓名输入
        session['data']['name'] = user_input
        session['state'] = 'skill_input'
        return jsonify({
            'message': f'您好，{user_input}！',
            'next_prompt': '请输入您想学习的技能 (如 "Python 编程"):'
        })

    elif state == 'skill_input':
        # 处理技能输入
        session['data']['skill_name'] = user_input
        session['state'] = 'model_selection'
        return jsonify({
            'message': f'您选择学习的技能是: {user_input}',
            'next_prompt': '请选择要使用的模型:\n1. DeepSeek Chat (默认)\n2. GLM-4-Long',
            'options': ['1', '2']
        })

    elif state == 'model_selection':
        # 处理模型选择
        model_choice = user_input.strip()
        if model_choice == "2":
            model = "glm-4-long"
        else:
            model = "deepseek-chat"  # 默认模型

        session['data']['model'] = model
        session['state'] = 'skill_assessment_q1'

        return jsonify({
            'message': f'您选择了模型: {model}',
            'next_prompt': '请回答以下问题来评估您的技能水平 (回答 y/n):\n问题1: 您是否了解编程基础概念? (y/n)',
            'options': ['y', 'n']
        })

    elif state == 'skill_assessment_q1':
        # 问题1回答
        session['data']['q1'] = user_input.lower() == 'y'
        session['state'] = 'skill_assessment_q2'
        return jsonify({
            'message': '已记录您的回答',
            'next_prompt': '问题2: 您是否使用过类似的编程语言? (y/n)',
            'options': ['y', 'n']
        })

    elif state == 'skill_assessment_q2':
        # 问题2回答
        session['data']['q2'] = user_input.lower() == 'y'
        session['state'] = 'skill_assessment_q3'
        return jsonify({
            'message': '已记录您的回答',
            'next_prompt': '问题3: 您是否完成过相关项目? (y/n)',
            'options': ['y', 'n']
        })

    elif state == 'skill_assessment_q3':
        # 问题3回答
        session['data']['q3'] = user_input.lower() == 'y'

        # 创建用户配置文件和评估技能水平
        user = UserProfile(session['data']['name'])
        answers = {
            'q1': session['data']['q1'],
            'q2': session['data']['q2'],
            'q3': session['data']['q3']
        }
        skill_level = user.assess_skill_level(answers)
        session['data']['skill_level'] = skill_level
        session['data']['user_profile'] = user
        session['data']['learning_goals'] = []
        session['state'] = 'learning_goals'

        return jsonify({
            'message': f'根据您的回答，系统评估您的技能水平为: {skill_level}',
            'next_prompt': '请输入您的学习目标 (输入空行结束):'
        })

    elif state == 'learning_goals':
        if not user_input.strip():
            # 空行表示结束学习目标输入
            session['state'] = 'generating_course'

            # 准备生成课程
            user = session['data']['user_profile']
            skill_name = session['data']['skill_name']
            skill = Skill(skill_name, f"{skill_name}基础知识")

            # 获取API密钥
            api_key = os.getenv("GLM_API_KEY")
            model = session['data']['model']

            # 生成课程
            return jsonify({
                'message': f'开始为{user.name}生成{skill_name}课程...',
                'next_prompt': '正在生成课程，请稍候...',
                'processing': True
            })
        else:
            # 添加学习目标
            session['data']['learning_goals'].append(user_input)
            session['data']['user_profile'].add_learning_goal(user_input)
            return jsonify({
                'message': f'已添加学习目标: {user_input}',
                'next_prompt': '请输入您的下一个学习目标 (输入空行结束):'
            })

    elif state == 'generating_course':
        # 这个状态由前端发起请求触发
        user = session['data']['user_profile']
        skill_name = session['data']['skill_name']
        skill = Skill(skill_name, f"{skill_name}基础知识")

        # 获取API密钥
        api_key = os.getenv("GLM_API_KEY")
        model = session['data']['model']

        # 生成课程
        ai_generator = AIGenerator(max_iterations=1, api_key=api_key, model=model)
        manager = CourseGenerationManager(max_iterations=1, user_profile=user, skill=skill, aigenerator=ai_generator)
        course = manager.generate_course()

        # 导出为OLX
        exporter = OLXExporter(course, output_dir=f"output/{course.course}")
        tar_path = exporter.export_to_tar_gz()

        # 存储结果信息
        session['data']['course'] = course
        session['data']['tar_path'] = tar_path
        session['state'] = 'completed'

        return jsonify({
            'message': f'课程已生成完成！',
            'next_prompt': '您可以下载课程包或查看课程信息:',
            'course_title': course.title,
            'chapter_count': len(course.chapters),
            'download_url': f'/api/download/{session_id}'
        })


@app.route('/api/generate_course/<session_id>', methods=['POST'])
def generate_course(session_id):
    """生成课程（异步处理）"""
    if session_id not in sessions:
        return jsonify({'error': '会话不存在或已过期'}), 400

    session = sessions[session_id]

    user = session['data']['user_profile']
    skill_name = session['data']['skill_name']
    skill = Skill(skill_name, f"{skill_name}基础知识")

    # 获取API密钥
    api_key = os.getenv("GLM_API_KEY")
    model = session['data']['model']

    # 生成课程
    ai_generator = AIGenerator(max_iterations=1, api_key=api_key, model=model)
    manager = CourseGenerationManager(max_iterations=1, user_profile=user, skill=skill, aigenerator=ai_generator)
    course = manager.generate_course()

    # 导出为OLX
    exporter = OLXExporter(course, output_dir=f"output/{course.course}")
    tar_path = exporter.export_to_tar_gz()

    # 存储结果信息
    session['data']['course'] = course
    session['data']['tar_path'] = tar_path
    session['state'] = 'completed'

    return jsonify({
        'message': f'课程已生成完成！',
        'course_title': course.title,
        'chapter_count': len(course.chapters),
        'download_url': f'/api/download/{session_id}'
    })


@app.route('/api/download/<session_id>', methods=['GET'])
def download_course(session_id):
    """下载课程包"""
    if session_id not in sessions or 'tar_path' not in sessions[session_id]['data']:
        return jsonify({'error': '课程不存在或尚未生成'}), 400

    tar_path = sessions[session_id]['data']['tar_path']
    return send_file(tar_path, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True, port=5000)