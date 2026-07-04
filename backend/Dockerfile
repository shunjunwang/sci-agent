FROM python:3.11-slim

WORKDIR /app

# 配置 pip 国内镜像
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# 先复制依赖文件以利用 Docker 层缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制源码
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
