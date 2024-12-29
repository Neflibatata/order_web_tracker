// 格式化时间函数
function formatTime(seconds) {
    if (seconds < 60) {
        return Math.round(seconds) + " 秒";
    } else if (seconds < 3600) {
        return Math.round(seconds / 60) + " 分钟";
    } else {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.round((seconds % 3600) / 60);
        return hours + " 小时 " + minutes + " 分钟";
    }
}

// 更新进度显示
function updateProgressDisplay(data) {
    // 更新进度条
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const percentage = Math.round(data.percentage);
    progressBar.style.width = percentage + '%';
    progressText.textContent = percentage + '%';

    // 更新统计信息
    document.getElementById('currentRecords').textContent = data.current;
    document.getElementById('totalRecords').textContent = data.total;
    document.getElementById('successfulQueries').textContent = data.successful;
    document.getElementById('failedQueries').textContent = data.failed;
    document.getElementById('avgQueryTime').textContent = data.avg_time.toFixed(2);
    document.getElementById('estimatedTime').textContent = formatTime(data.estimated_remaining_time);
}

// 显示错误消息
function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

// 隐藏错误消息
function hideError() {
    document.getElementById('errorMessage').style.display = 'none';
}

// 检查进度
function checkProgress() {
    fetch('/progress_status')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showError(data.error);
                return;
            }

            hideError();
            updateProgressDisplay(data);

            if (data.complete) {
                // 显示下载按钮
                const downloadSection = document.getElementById('downloadSection');
                const downloadButton = document.getElementById('downloadButton');
                downloadButton.href = data.download_url;
                downloadSection.style.display = 'block';
            } else if (data.is_processing) {
                // 继续检查进度
                setTimeout(checkProgress, 1000);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('获取进度信息失败，请刷新页面重试');
        });
}

// 处理文件上传
document.getElementById('uploadForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // 隐藏之前的错误消息和下载按钮
    hideError();
    document.getElementById('downloadSection').style.display = 'none';
    
    const formData = new FormData(this);
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // 显示进度区域
            document.getElementById('progressSection').style.display = 'block';
            // 开始检查进度
            checkProgress();
        } else {
            throw new Error(result.error || '上传失败');
        }
    } catch (error) {
        showError(error.message);
    }
}); 