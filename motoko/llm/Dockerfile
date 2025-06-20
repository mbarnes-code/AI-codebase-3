FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY llm_server.py ./

EXPOSE 8000
CMD ["uvicorn", "llm_server:app", "--host", "0.0.0.0", "--port", "8000"]
