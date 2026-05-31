# -*- coding: utf-8 -*-
"""
Flask后端API - 提供前后端分离的RESTful接口
"""
import sys
import os
import json
import requests
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime

# 添加backend目录到路径
sys.path.insert(0, os.path.dirname(__file__))
from database import init_db, migrate_db, get_db_connection, log_message
from collector import collect_daily_data
from bs4 import BeautifulSoup
from config import MATERIALS_BASE_DIR

# 文件上传配置
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'zip', 'rar', '7z', 'png', 'jpg', 'jpeg'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 创建Flask应用
app = Flask(__name__, 
            static_folder='../frontend',
            static_url_path='')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# 配置CORS（允许跨域请求）
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ==================== 首页 ====================
@app.route('/')
def index():
    """返回前端页面"""
    return send_from_directory(app.static_folder, 'index.html')

# ==================== 竞赛管理API ====================
@app.route('/api/competitions', methods=['GET'])
def get_competitions():
    """获取所有竞赛列表，按截止日期升序排列（最近的日期在前）"""
    try:
        conn = get_db_connection()
        competitions = conn.execute(
            '''SELECT * FROM competitions 
               ORDER BY 
                   CASE 
                       WHEN end_date IS NULL OR end_date = '' THEN 1 
                       ELSE 0 
                   END,
                   end_date ASC'''
        ).fetchall()
        conn.close()

        result = [dict(row) for row in competitions]
        log_message("信息", "获取竞赛列表成功", "竞赛管理")
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        log_message("错误", f"获取竞赛列表失败: {str(e)}", "竞赛管理")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/competitions', methods=['POST'])
def create_competition():
    """创建新竞赛"""
    try:
        data = request.get_json()
        required_fields = ['name']
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'message': '缺少必要字段: name'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO competitions 
               (name, official_url, description, category, official_materials, official_materials_path,
                folder_path, status, start_date, end_date) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                data.get('name'),
                data.get('official_url', ''),
                data.get('description', ''),
                data.get('category', ''),
                data.get('official_materials', ''),
                data.get('official_materials_path', ''),
                data.get('folder_path', ''),
                data.get('status', 'active'),
                data.get('start_date', ''),
                data.get('end_date', '')
            )
        )
        conn.commit()
        competition_id = cursor.lastrowid
        conn.close()
        
        log_message("信息", f"创建竞赛成功: {data.get('name')}", "竞赛管理")
        return jsonify({'success': True, 'id': competition_id, 'message': '竞赛创建成功'})
    except Exception as e:
        log_message("错误", f"创建竞赛失败: {str(e)}", "竞赛管理")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/competitions/<int:competition_id>', methods=['PUT'])
def update_competition(competition_id):
    """更新竞赛信息"""
    try:
        data = request.get_json()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            '''UPDATE competitions 
               SET name=?, official_url=?, description=?, category=?, official_materials=?,
                   official_materials_path=?, folder_path=?,
                   status=?, start_date=?, end_date=?, updated_at=CURRENT_TIMESTAMP
               WHERE id=?''',
            (
                data.get('name'),
                data.get('official_url'),
                data.get('description'),
                data.get('category'),
                data.get('official_materials'),
                data.get('official_materials_path', ''),
                data.get('folder_path', ''),
                data.get('status'),
                data.get('start_date'),
                data.get('end_date'),
                competition_id
            )
        )
        conn.commit()
        conn.close()
        
        log_message("信息", f"更新竞赛成功，ID: {competition_id}", "竞赛管理")
        return jsonify({'success': True, 'message': '竞赛更新成功'})
    except Exception as e:
        log_message("错误", f"更新竞赛失败: {str(e)}", "竞赛管理")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/competitions/<int:competition_id>', methods=['DELETE'])
def delete_competition(competition_id):
    """删除竞赛"""
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM competitions WHERE id = ?', (competition_id,))
        conn.commit()
        conn.close()
        
        log_message("信息", f"删除竞赛成功，ID: {competition_id}", "竞赛管理")
        return jsonify({'success': True, 'message': '竞赛删除成功'})
    except Exception as e:
        log_message("错误", f"删除竞赛失败: {str(e)}", "竞赛管理")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== 学生管理API ====================
@app.route('/api/students', methods=['GET'])
def get_students():
    """获取所有学生列表"""
    try:
        conn = get_db_connection()
        students = conn.execute(
            'SELECT * FROM students ORDER BY created_at DESC'
        ).fetchall()
        conn.close()
        
        result = [dict(row) for row in students]
        log_message("信息", "获取学生列表成功", "学生管理")
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        log_message("错误", f"获取学生列表失败: {str(e)}", "学生管理")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/students', methods=['POST'])
def create_student():
    """创建新学生"""
    try:
        data = request.get_json()
        required_fields = ['name']
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'message': '缺少必要字段: name'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO students 
               (name, grade, major, phone, email) 
               VALUES (?, ?, ?, ?, ?)''',
            (
                data.get('name'),
                data.get('grade', ''),
                data.get('major', ''),
                data.get('phone', ''),
                data.get('email', '')
            )
        )
        conn.commit()
        student_id = cursor.lastrowid
        conn.close()
        
        log_message("信息", f"创建学生成功: {data.get('name')}", "学生管理")
        return jsonify({'success': True, 'id': student_id, 'message': '学生创建成功'})
    except Exception as e:
        log_message("错误", f"创建学生失败: {str(e)}", "学生管理")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/students/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    """更新学生信息"""
    try:
        data = request.get_json()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            '''UPDATE students 
               SET name=?, grade=?, major=?, phone=?, email=?, updated_at=CURRENT_TIMESTAMP
               WHERE id=?''',
            (
                data.get('name'),
                data.get('grade'),
                data.get('major'),
                data.get('phone'),
                data.get('email'),
                student_id
            )
        )
        conn.commit()
        conn.close()
        
        log_message("信息", f"更新学生成功，ID: {student_id}", "学生管理")
        return jsonify({'success': True, 'message': '学生信息更新成功'})
    except Exception as e:
        log_message("错误", f"更新学生失败: {str(e)}", "学生管理")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    """删除学生"""
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM students WHERE id = ?', (student_id,))
        conn.commit()
        conn.close()
        
        log_message("信息", f"删除学生成功，ID: {student_id}", "学生管理")
        return jsonify({'success': True, 'message': '学生删除成功'})
    except Exception as e:
        log_message("错误", f"删除学生失败: {str(e)}", "学生管理")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== 学生竞赛关联API ====================
@app.route('/api/student-competitions', methods=['GET'])
def get_student_competitions():
    """获取学生竞赛关联列表，支持按竞赛ID过滤"""
    try:
        competition_id = request.args.get('competition_id', type=int)
        student_id = request.args.get('student_id', type=int)
        
        conn = get_db_connection()
        
        if competition_id:
            relations = conn.execute('''
                SELECT sc.*, s.name as student_name, s.grade, s.major, s.email,
                       c.name as competition_name, c.official_url, c.end_date
                FROM student_competitions sc
                LEFT JOIN students s ON sc.student_id = s.id
                LEFT JOIN competitions c ON sc.competition_id = c.id
                WHERE sc.competition_id = ?
                ORDER BY sc.created_at DESC
            ''', (competition_id,)).fetchall()
        elif student_id:
            relations = conn.execute('''
                SELECT sc.*, s.name as student_name, s.grade, s.major, s.email,
                       c.name as competition_name, c.official_url, c.end_date
                FROM student_competitions sc
                LEFT JOIN students s ON sc.student_id = s.id
                LEFT JOIN competitions c ON sc.competition_id = c.id
                WHERE sc.student_id = ?
                ORDER BY sc.created_at DESC
            ''', (student_id,)).fetchall()
        else:
            relations = conn.execute('''
                SELECT sc.*, s.name as student_name, s.grade, s.major, s.email,
                       c.name as competition_name, c.official_url, c.end_date
                FROM student_competitions sc
                LEFT JOIN students s ON sc.student_id = s.id
                LEFT JOIN competitions c ON sc.competition_id = c.id
                ORDER BY sc.created_at DESC
            ''').fetchall()
        
        conn.close()
        
        result = [dict(row) for row in relations]
        log_message("信息", "获取学生竞赛关联列表成功", "关联管理")
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        log_message("错误", f"获取学生竞赛关联列表失败: {str(e)}", "关联管理")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/student-competitions', methods=['POST'])
def create_student_competition():
    """创建学生竞赛关联"""
    try:
        data = request.get_json()
        required_fields = ['student_id', 'competition_id']
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'message': '缺少必要字段: student_id, competition_id'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO student_competitions 
               (student_id, competition_id, project_name, project_folder, role, registration_status, progress, project_url, material_files, remarks) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                data.get('student_id'),
                data.get('competition_id'),
                data.get('project_name', ''),
                data.get('project_folder', ''),
                data.get('role', ''),
                data.get('registration_status', 'pending'),
                data.get('progress', 'not_started'),
                data.get('project_url', ''),
                data.get('material_files', ''),
                data.get('remarks', '')
            )
        )
        conn.commit()
        relation_id = cursor.lastrowid
        conn.close()
        
        log_message("信息", f"创建学生竞赛关联成功", "关联管理")
        return jsonify({'success': True, 'id': relation_id, 'message': '关联创建成功'})
    except Exception as e:
        log_message("错误", f"创建学生竞赛关联失败: {str(e)}", "关联管理")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/student-competitions/<int:relation_id>', methods=['PUT'])
def update_student_competition(relation_id):
    """更新学生竞赛关联"""
    try:
        data = request.get_json()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            '''UPDATE student_competitions 
               SET project_name=?, project_folder=?, role=?, registration_status=?, progress=?, 
                   project_url=?, material_files=?, remarks=?, updated_at=CURRENT_TIMESTAMP
               WHERE id=?''',
            (
                data.get('project_name'),
                data.get('project_folder', ''),
                data.get('role'),
                data.get('registration_status'),
                data.get('progress'),
                data.get('project_url'),
                data.get('material_files'),
                data.get('remarks'),
                relation_id
            )
        )
        conn.commit()
        conn.close()
        
        log_message("信息", f"更新学生竞赛关联成功，ID: {relation_id}", "关联管理")
        return jsonify({'success': True, 'message': '关联更新成功'})
    except Exception as e:
        log_message("错误", f"更新学生竞赛关联失败: {str(e)}", "关联管理")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/student-competitions/<int:relation_id>', methods=['DELETE'])
def delete_student_competition(relation_id):
    """删除学生竞赛关联"""
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM student_competitions WHERE id = ?', (relation_id,))
        conn.commit()
        conn.close()
        
        log_message("信息", f"删除学生竞赛关联成功，ID: {relation_id}", "关联管理")
        return jsonify({'success': True, 'message': '关联删除成功'})
    except Exception as e:
        log_message("错误", f"删除学生竞赛关联失败: {str(e)}", "关联管理")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== 竞赛详情API（包含参赛学生） ====================
@app.route('/api/competitions/<int:competition_id>/students', methods=['GET'])
def get_competition_students(competition_id):
    """获取某个竞赛的所有参赛学生信息，同时自动扫描官方材料目录"""
    try:
        conn = get_db_connection()

        # 获取竞赛信息
        competition = conn.execute(
            'SELECT * FROM competitions WHERE id = ?', (competition_id,)
        ).fetchone()

        if not competition:
            conn.close()
            return jsonify({'success': False, 'message': '竞赛不存在'}), 404

        # 获取参赛学生列表
        students = conn.execute('''
            SELECT sc.id as relation_id, sc.project_name, sc.role, sc.registration_status,
                   sc.progress, sc.project_url, sc.material_files, sc.remarks, sc.created_at,
                   s.id as student_id, s.name as student_name, s.grade, s.major, s.phone, s.email
            FROM student_competitions sc
            LEFT JOIN students s ON sc.student_id = s.id
            WHERE sc.competition_id = ?
            ORDER BY sc.created_at DESC
        ''', (competition_id,)).fetchall()

        conn.close()

        comp_dict = dict(competition)

        # 自动扫描官方材料目录
        base_path = resolve_competition_folder(comp_dict)
        official_materials_files = []
        if base_path and os.path.exists(base_path):
            official_dir = os.path.join(base_path, '00_官方材料')
            if os.path.isdir(official_dir):
                for name in sorted(os.listdir(official_dir)):
                    item_path = os.path.join(official_dir, name)
                    if name.startswith('.') or name in ('__pycache__', 'node_modules', '.git', 'logs'):
                        continue
                    if os.path.isfile(item_path):
                        rel_path = '00_官方材料/' + name
                        official_materials_files.append({
                            'name': name,
                            'path': rel_path,
                            'size': os.path.getsize(item_path)
                        })

        comp_dict['official_materials_files'] = official_materials_files

        result = {
            'competition': comp_dict,
            'students': [dict(row) for row in students]
        }

        log_message("信息", f"获取竞赛{competition_id}参赛学生列表成功", "关联管理")
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        log_message("错误", f"获取竞赛参赛学生列表失败: {str(e)}", "关联管理")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== 材料上传API ====================
@app.route('/api/upload-material/<int:relation_id>', methods=['POST'])
def upload_material(relation_id):
    """上传参赛材料"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '没有文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '文件名为空'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': f'不支持的文件类型，允许: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
        
        # 创建上传目录
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # 安全文件名
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        
        # 保存文件
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(filepath)
        
        # 更新数据库中的材料文件路径
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取现有材料列表
        existing = conn.execute(
            'SELECT material_files FROM student_competitions WHERE id = ?', (relation_id,)
        ).fetchone()
        
        if existing and existing['material_files']:
            try:
                materials = json.loads(existing['material_files'])
            except:
                materials = []
        else:
            materials = []
        
        materials.append(unique_filename)
        
        cursor.execute(
            'UPDATE student_competitions SET material_files = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (json.dumps(materials, ensure_ascii=False), relation_id)
        )
        conn.commit()
        conn.close()
        
        log_message("信息", f"上传材料成功，关联ID: {relation_id}", "材料管理")
        return jsonify({
            'success': True, 
            'message': '材料上传成功',
            'filename': unique_filename
        })
    except Exception as e:
        log_message("错误", f"上传材料失败: {str(e)}", "材料管理")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/materials/<int:relation_id>', methods=['GET'])
def get_materials(relation_id):
    """获取参赛材料列表"""
    try:
        conn = get_db_connection()
        result = conn.execute(
            'SELECT material_files FROM student_competitions WHERE id = ?', (relation_id,)
        ).fetchone()
        conn.close()
        
        if result and result['material_files']:
            try:
                materials = json.loads(result['material_files'])
            except:
                materials = []
        else:
            materials = []
        
        return jsonify({'success': True, 'data': materials})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/download-material/<filename>', methods=['GET'])
def download_material(filename):
    """下载材料文件"""
    try:
        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
    except Exception as e:
        return jsonify({'success': False, 'message': '文件不存在'}), 404

# ==================== 数据采集API ====================
@app.route('/api/collect', methods=['POST'])
def trigger_collection():
    """触发数据采集"""
    try:
        log_message("信息", "用户触发数据采集任务", "数据采集")
        result = collect_daily_data()
        return jsonify(result)
    except Exception as e:
        log_message("错误", f"数据采集失败: {str(e)}", "数据采集")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/collected-data', methods=['GET'])
def get_collected_data():
    """获取采集的数据列表（按赛事分组）"""
    try:
        conn = get_db_connection()
        data = conn.execute(
            'SELECT cd.*, c.name as competition_name FROM collected_data cd '
            'LEFT JOIN competitions c ON cd.competition_id = c.id '
            'ORDER BY cd.collected_at DESC'
        ).fetchall()
        conn.close()

        grouped = {}
        for row in data:
            d = dict(row)
            cid = d.get('competition_id') or 0
            if cid not in grouped:
                cname = d.get('competition_name') or '通用资讯'
                grouped[cid] = {
                    'competition_id': cid,
                    'competition_name': cname,
                    'news': []
                }
            grouped[cid]['news'].append(d)

        result = list(grouped.values())
        result.sort(key=lambda x: (x['competition_id'] == 0, -len(x['news'])))

        log_message("信息", f"获取采集数据成功，{len(result)} 个赛事分组", "数据采集")
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        log_message("错误", f"获取采集数据失败: {str(e)}", "数据采集")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/competition-news/<int:competition_id>', methods=['GET'])
def get_competition_news(competition_id):
    """获取指定赛事的资讯"""
    try:
        conn = get_db_connection()
        comp = conn.execute('SELECT id, name FROM competitions WHERE id = ?', (competition_id,)).fetchone()
        if not comp:
            conn.close()
            return jsonify({'success': False, 'message': '赛事不存在'}), 404

        data = conn.execute(
            'SELECT * FROM collected_data WHERE competition_id = ? ORDER BY collected_at DESC',
            (competition_id,)
        ).fetchall()
        conn.close()

        return jsonify({
            'success': True,
            'competition': {'id': comp['id'], 'name': comp['name']},
            'data': [dict(row) for row in data]
        })
    except Exception as e:
        log_message("错误", f"获取赛事资讯失败: {str(e)}", "数据采集")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== 统计API ====================
@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """获取系统统计数据"""
    try:
        conn = get_db_connection()
        
        # 竞赛总数
        competition_count = conn.execute('SELECT COUNT(*) as count FROM competitions').fetchone()['count']
        
        # 学生总数
        student_count = conn.execute('SELECT COUNT(*) as count FROM students').fetchone()['count']
        
        # 采集数据总数
        data_count = conn.execute('SELECT COUNT(*) as count FROM collected_data').fetchone()['count']
        
        # 关联总数
        relation_count = conn.execute('SELECT COUNT(*) as count FROM student_competitions').fetchone()['count']
        
        conn.close()
        
        log_message("信息", "获取统计数据成功", "统计")
        return jsonify({
            'success': True,
            'data': {
                'competitions': competition_count,
                'students': student_count,
                'collected_data': data_count,
                'relations': relation_count
            }
        })
    except Exception as e:
        log_message("错误", f"获取统计数据失败: {str(e)}", "统计")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== 日志API ====================
@app.route('/api/logs', methods=['GET'])
def get_logs():
    """获取系统日志"""
    try:
        limit = request.args.get('limit', 100, type=int)
        conn = get_db_connection()
        logs = conn.execute(
            'SELECT * FROM system_logs ORDER BY created_at DESC LIMIT ?',
            (limit,)
        ).fetchall()
        conn.close()
        
        result = [dict(row) for row in logs]
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== 健康检查 ====================
@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'success': True,
        'message': '系统运行正常',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

# ==================== 文件浏览API ====================

def resolve_competition_folder(comp):
    """解析竞赛材料目录路径
    
    优先级：
    1. 数据库中的 folder_path（若存在且有效）
    2. config.py 中的 MATERIALS_BASE_DIR + 竞赛名称
    """
    comp = dict(comp)
    db_path = (comp.get('folder_path') or '').strip()
    if db_path and os.path.exists(db_path):
        return db_path
    
    name = (comp.get('name') or '').strip()
    if name:
        fallback = os.path.join(MATERIALS_BASE_DIR, name)
        if os.path.exists(fallback):
            return fallback
        return fallback
    
    return db_path if db_path else ''

@app.route('/api/files/browse', methods=['GET'])
def browse_competition_files():
    """浏览竞赛目录下文件"""
    try:
        competition_id = request.args.get('competition_id', type=int)
        subdir = request.args.get('subdir', '')  # 相对子目录，如 "00_官方材料" 或 "00_参赛学生/xxx"
        
        conn = get_db_connection()
        comp = conn.execute('SELECT * FROM competitions WHERE id = ?', (competition_id,)).fetchone()
        conn.close()
        
        if not comp:
            return jsonify({'success': False, 'message': '竞赛不存在'}), 404
        
        base_path = resolve_competition_folder(comp)
        if not base_path or not os.path.exists(base_path):
            hint = f"请在 config.py 中设置 MATERIALS_BASE_DIR，并在该目录下创建 \"{comp['name']}\" 文件夹"
            return jsonify({'success': False, 'message': f'竞赛材料目录不存在: {base_path}', 'hint': hint}), 404
        
        # 构建完整路径
        full_path = os.path.normpath(os.path.join(base_path, subdir)) if subdir else base_path
        if not full_path.startswith(os.path.normpath(base_path)):  # 防路径穿越
            return jsonify({'success': False, 'message': '不允许访问上级目录'}), 403
        
        if not os.path.exists(full_path):
            return jsonify({'success': False, 'message': '路径不存在'}), 404
        
        items = []
        for name in sorted(os.listdir(full_path)):
            item_path = os.path.join(full_path, name)
            if name.startswith('.') or name in ('__pycache__', 'node_modules', '.git', 'logs'):
                continue
            item_type = 'folder' if os.path.isdir(item_path) else 'file'
            rel_path = os.path.relpath(item_path, base_path).replace('\\', '/')
            size = os.path.getsize(item_path) if item_type == 'file' else None
            items.append({
                'name': name,
                'type': item_type,
                'path': rel_path,
                'size': size
            })
        
        return jsonify({'success': True, 'data': {
            'current_path': os.path.relpath(full_path, base_path).replace('\\', '/'),
            'base_path': base_path,
            'items': items
        }})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/files/serve/<int:competition_id>', methods=['GET'])
def serve_competition_file(competition_id):
    """直接提供竞赛目录下文件"""
    try:
        file_path = request.args.get('path', '')
        if not file_path:
            return jsonify({'success': False, 'message': '缺少文件路径'}), 400
        
        conn = get_db_connection()
        comp = conn.execute('SELECT * FROM competitions WHERE id = ?', (competition_id,)).fetchone()
        conn.close()
        
        if not comp:
            return jsonify({'success': False, 'message': '竞赛不存在'}), 404
        
        base_path = resolve_competition_folder(comp)
        if not base_path or not os.path.exists(base_path):
            return jsonify({'success': False, 'message': f'竞赛材料目录不存在'}), 404
        
        full_path = os.path.normpath(os.path.join(base_path, file_path))
        if not full_path.startswith(os.path.normpath(base_path)):
            return jsonify({'success': False, 'message': '不允许访问上级目录'}), 403
        
        if not os.path.isfile(full_path):
            return jsonify({'success': False, 'message': '文件不存在'}), 404
        
        return send_from_directory(os.path.dirname(full_path), os.path.basename(full_path))
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== 赛程规划API ====================
TIME_PLAN_URL = 'https://cpipc.acge.org.cn/pw/notice/detail/2c9080179e403028019e484cf50210a6?page=1'

@app.route('/api/time-plan', methods=['GET'])
def get_time_plan():
    """获取赛程规划数据"""
    try:
        conn = get_db_connection()
        plan = conn.execute(
            'SELECT * FROM time_plan ORDER BY id DESC LIMIT 1'
        ).fetchone()
        conn.close()

        if plan:
            data = json.loads(plan['plan_data'])
            remarks = json.loads(plan['remarks']) if plan['remarks'] else {}
            for item in data:
                seq = item.get('seq', '')
                item['remark'] = remarks.get(seq, '')
            return jsonify({
                'success': True,
                'data': data,
                'source_url': plan['source_url'],
                'updated_at': plan['updated_at']
            })
        else:
            return jsonify({
                'success': True,
                'data': [],
                'source_url': TIME_PLAN_URL,
                'updated_at': None
            })
    except Exception as e:
        log_message("错误", f"获取赛程规划失败: {str(e)}", "赛程规划")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/time-plan/remark', methods=['POST'])
def save_time_plan_remark():
    """保存某条赛程的个人备注"""
    try:
        body = request.get_json(force=True)
        seq = str(body.get('seq', ''))
        remark = body.get('remark', '')

        if not seq:
            return jsonify({'success': False, 'message': '缺少序号参数'}), 400

        conn = get_db_connection()
        plan = conn.execute(
            'SELECT * FROM time_plan ORDER BY id DESC LIMIT 1'
        ).fetchone()

        if not plan:
            conn.close()
            return jsonify({'success': False, 'message': '暂无赛程数据'}), 404

        remarks = json.loads(plan['remarks']) if plan['remarks'] else {}
        if remark:
            remarks[seq] = remark
        else:
            remarks.pop(seq, None)

        conn.execute(
            'UPDATE time_plan SET remarks = ? WHERE id = ?',
            (json.dumps(remarks, ensure_ascii=False), plan['id'])
        )
        conn.commit()
        conn.close()

        log_message("信息", f"赛程备注已保存 (序号 {seq})", "赛程规划")
        return jsonify({'success': True, 'message': '备注保存成功'})
    except Exception as e:
        log_message("错误", f"保存赛程备注失败: {str(e)}", "赛程规划")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/time-plan/refresh', methods=['POST'])
def refresh_time_plan():
    """从官网刷新赛程规划数据"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        resp = requests.get(TIME_PLAN_URL, headers=headers, timeout=20)
        resp.encoding = 'utf-8'

        if resp.status_code != 200:
            return jsonify({'success': False, 'message': f'官网返回状态码: {resp.status_code}'}), 502

        soup = BeautifulSoup(resp.text, 'lxml')
        table = soup.find('table')
        if not table:
            return jsonify({'success': False, 'message': '未找到赛程表格'}), 502

        rows = table.find_all('tr')
        plan_data = []
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 5:
                name = cells[1].get_text(strip=True)
                if '主题赛事' in name:
                    continue
                plan_data.append({
                    'seq': cells[0].get_text(strip=True),
                    'name': name,
                    'register_time': cells[2].get_text(strip=True) or '待定',
                    'submit_time': cells[3].get_text(strip=True) or '待定',
                    'final_time': cells[4].get_text(strip=True) or '待定'
                })

        if not plan_data:
            return jsonify({'success': False, 'message': '解析表格无数据'}), 502

        plan_json = json.dumps(plan_data, ensure_ascii=False)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = get_db_connection()
        conn.execute(
            'INSERT INTO time_plan (plan_data, source_url, updated_at) VALUES (?, ?, ?)',
            (plan_json, TIME_PLAN_URL, now)
        )
        conn.commit()
        conn.close()

        log_message("信息", f"赛程规划刷新成功，共 {len(plan_data)} 条记录", "赛程规划")
        return jsonify({
            'success': True,
            'data': plan_data,
            'updated_at': now,
            'message': f'刷新成功，共 {len(plan_data)} 条赛程记录'
        })
    except requests.exceptions.RequestException as e:
        log_message("错误", f"赛程规划刷新失败(网络): {str(e)}", "赛程规划")
        return jsonify({'success': False, 'message': f'网络请求失败: {str(e)}'}), 502
    except Exception as e:
        log_message("错误", f"赛程规划刷新失败: {str(e)}", "赛程规划")
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== 初始化 ====================
if __name__ == '__main__':
    print("正在初始化竞赛管理系统...")
    init_db()
    migrate_db()
    log_message("信息", "系统启动", "系统")
    print("系统启动成功，访问地址: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
