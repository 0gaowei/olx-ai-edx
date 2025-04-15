from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import uuid
from dotenv import load_dotenv

from olx_ai_edx.models import UserProfile, Skill
from olx_ai_edx.ai_gen import AIGenerator, CourseGenerationManager, UserInteractionManager
from olx_ai_edx.export import OLXExporter

# 加载环境变量
load_dotenv(os.path.join(os.path.dirname(__file__), 'olx_ai_edx', 'ref', '.env'))

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://127.0.0.1:5500"}})

# 存储用户会话状态
sessions = {}

@app.route('/api/start_session', methods=['POST'])
def start_session():
    """开始新的会话"""
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        'state': 'welcome',
        'data': {},
        'interaction_manager': UserInteractionManager(max_iterations=1)
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
    interaction_manager = session['interaction_manager']

    if state == 'welcome':
        session['data']['name'] = user_input
        session['state'] = 'skill_input'
        return jsonify({
            'message': f'您好，{user_input}！',
            'next_prompt': '请输入您想学习的技能 (如 "Python 编程"):'
        })

    elif state == 'skill_input':
        session['data']['skill_name'] = user_input
        session['state'] = 'model_selection'
        return jsonify({
            'message': f'您选择学习的技能是: {user_input}',
            'next_prompt': '请选择要使用的模型:\n1. DeepSeek Chat (默认)\n2. GLM-4-Long',
            'options': ['1', '2']
        })

    elif state == 'model_selection':
        model_choice = user_input.strip()
        if model_choice == "2":
            model = "glm-4-long"
            api_key = os.getenv("GLM_API_KEY")
            base_url = "https://open.bigmodel.cn/api/paas/v4"  # GLM实际API地址
        else:
            model = "deepseek-chat"
            api_key = os.getenv("DEEPSEEK_API_KEY")
            base_url = "https://api.deepseek.com/v1"  # DeepSeek实际API地址

        session['data']['model'] = model
        session['data']['api_key'] = api_key
        session['data']['base_url'] = base_url  # 存储BASE_URL

        ai_generator = AIGenerator(
            api_key=api_key,
            model=model,
            base_url=base_url  # 传递给AIGenerator构造函数
        )
        session['interaction_manager'].aigenerator = ai_generator

        assessment_questions = interaction_manager.aigenerator.generate_assessment_questions(session['data']['skill_name'])
        # 新增：检查问题列表有效性
        if not assessment_questions or len(assessment_questions) == 0:
            return jsonify({
                'error': '无法生成评估问题，请重试或联系管理员'
            }), 500

        session['data']['assessment_questions'] = assessment_questions
        session['data']['current_question_index'] = 0
        session['data']['user_responses'] = []

        session['state'] = 'skill_assessment'
        return jsonify({
            'message': f'您选择了模型: {model}',
            'next_prompt': f'请回答以下问题来评估您的技能水平:\n{assessment_questions[0]}'  # 此时列表已确保非空
        })

    elif state == 'skill_assessment':
        current_index = session['data']['current_question_index']
        session['data']['user_responses'].append({
            'question': session['data']['assessment_questions'][current_index],
            'answer': user_input
        })

        if current_index < len(session['data']['assessment_questions']) - 1:
            next_index = current_index + 1
            session['data']['current_question_index'] = next_index
            return jsonify({
                'message': '已记录您的回答',
                'next_prompt': session['data']['assessment_questions'][next_index]
            })
        else:
            assessment_result = interaction_manager.aigenerator.analyze_user_responses(
                session['data']['skill_name'],
                session['data']['user_responses']
            )
            session['data']['assessment_result'] = assessment_result

            # user_profile = interaction_manager.create_user_profile(
            #     session['data']['name'],
            #     assessment_result['level'],
            #     session['data']['skill_name'],
            #     Skill(session['data']['skill_name'], assessment_result['learning_path'])
            # )
            # session['data']['user_profile'] = user_profile

            session['state'] = 'learning_goals'
            return jsonify({
                'message': f'根据评估，您在{session["data"]["skill_name"]}方面的水平为: {assessment_result["level"]}\n'
                            f'水平说明: {assessment_result["explanation"]}\n'
                            f'您的学习目标: {", ".join(assessment_result["objectives"])}\n'
                            f'推荐学习路径: {assessment_result["learning_path"]}',

            })

    elif state == 'learning_goals':
        if not user_input.strip():
            session['state'] = 'generating_course'
            return jsonify({
                'message': '开始生成课程...',
                'processing': True
            })
        else:
            if 'learning_goals' not in session['data']:
                session['data']['learning_goals'] = []
            session['data']['learning_goals'].append(user_input)
            return jsonify({
                'message': f'已添加学习目标: {user_input}',  # 删除 nextprompt

            })

    elif state == 'generating_course':
        user_profile = session['data']['user_profile']
        skill = Skill(session['data']['skill_name'], session['data']['assessment_result']['learning_path'])
        ai_generator = session['interaction_manager'].aigenerator
        course_manager = CourseGenerationManager(
            max_iterations=1,
            user_profile=user_profile,
            skill=skill,
            aigenerator=ai_generator
        )
        course = course_manager.generate_course()

        exporter = OLXExporter(course, output_dir=f"output/{course.course}")
        tar_path = exporter.export_to_tar_gz()

        session['data']['course'] = course
        session['data']['tar_path'] = tar_path
        session['state'] = 'completed'

        return jsonify({
            'message': '课程已生成完成！',
            'course_title': course.title,
            'chapter_count': len(course.chapters),
            'download_url': f'/api/download/{session_id}'
        })

    else:
        return jsonify({'error': '未知会话状态'}), 400

@app.route('/api/download/<session_id>', methods=['GET'])
def download_course(session_id):
    """下载课程包"""
    if session_id not in sessions or 'tar_path' not in sessions[session_id]['data']:
        return jsonify({'error': '课程不存在或尚未生成'}), 400

    tar_path = sessions[session_id]['data']['tar_path']
    return send_file(tar_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000)