import os
import time
from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from tracker import process_orders_file
import threading

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 用于flash消息
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传文件大小为16MB

# 确保上传目录存在
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# 全局变量用于存储处理进度
processing_status = {
    'is_processing': False,
    'current': 0,
    'total': 0,
    'successful': 0,
    'failed': 0,
    'avg_time': 0,
    'estimated_remaining_time': 0,
    'percentage': 0,
    'error': None,
    'output_filename': None
}

def update_progress(progress_data):
    """更新进度信息"""
    global processing_status
    processing_status.update(progress_data)

def process_file_with_progress(file_path):
    """处理文件并更新进度"""
    global processing_status
    processing_status['is_processing'] = True
    processing_status['error'] = None
    
    try:
        output_filename, stats = process_orders_file(file_path, update_progress)
        processing_status['output_filename'] = output_filename
        return output_filename, stats
    except Exception as e:
        processing_status['error'] = str(e)
        raise
    finally:
        # 删除原始上传文件
        try:
            os.remove(file_path)
        except:
            pass

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file and file.filename.endswith('.csv'):
        try:
            # 保存上传的文件
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # 在新线程中处理文件
            thread = threading.Thread(
                target=process_file_with_progress,
                args=(file_path,)
            )
            thread.start()
            
            return jsonify({'message': '文件上传成功，开始处理'})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': '只支持CSV文件'}), 400

@app.route('/progress_status')
def progress_status():
    """返回当前进度信息"""
    global processing_status
    
    # 如果处理完成且没有错误，返回结果文件名
    if not processing_status['is_processing'] and not processing_status['error'] and processing_status['output_filename']:
        return jsonify({
            **processing_status,
            'complete': True,
            'download_url': url_for('download_file', filename=processing_status['output_filename'])
        })
    
    return jsonify(processing_status)

@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_file(
            os.path.join(app.config['UPLOAD_FOLDER'], filename),
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': f'下载文件时出错: {str(e)}'}), 500

@app.route('/download_template')
def download_template():
    try:
        return send_file(
            'sample.csv',
            as_attachment=True,
            download_name='template.csv'
        )
    except Exception as e:
        return jsonify({'error': f'下载模板文件时出错: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 