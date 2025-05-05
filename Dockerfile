FROM python:3.13-bookworm
WORKDIR /root
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ ./src/
RUN isort --check-only --profile black --diff src/
RUN black --check src/
RUN mypy --check-untyped-defs src/
RUN flake8 src/
EXPOSE 8080
WORKDIR /root/src/
ENTRYPOINT ["flask", "--app", "endpoints", "run", "--host", "0.0.0.0", "-p", "8080", "--debug"]
