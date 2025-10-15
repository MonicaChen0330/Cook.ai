# 使用官方的 Python 3.10 slim 映像檔作為基底
FROM python:3.10-slim

# 在容器中建立一個工作目錄
WORKDIR /app

# 將依賴清單複製進去
COPY requirements.txt .

# 安裝所有依賴套件
RUN pip install --no-cache-dir -r requirements.txt

# 將你所有的程式碼複製進去
COPY . .

# 當容器啟動時，預設要執行的指令 (這裡以一個叫 app.py 的主程式為例)
CMD ["python3", "app.py"]