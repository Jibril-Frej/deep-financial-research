FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install .
EXPOSE 8080
CMD ["streamlit", "run", "src/app.py", "--server.port=8080", "--server.address=0.0.0.0"]