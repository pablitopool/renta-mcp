FROM python:3.11-slim

WORKDIR /app
ENV MCP_HOST=0.0.0.0

COPY pyproject.toml README.md ./
COPY helpers ./helpers
COPY tools ./tools
COPY resources ./resources
COPY data ./data
COPY main.py ./

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["python", "main.py"]
