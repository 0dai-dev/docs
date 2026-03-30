FROM python:3.12-slim

RUN useradd -m -u 1000 -s /bin/bash dev
USER dev
WORKDIR /workspace

CMD ["bash", "-lc", "python3 scripts/prepare_knowledge_issue.py && python3 scripts/score_knowledge_intake.py && python3 scripts/create_knowledge_issue.py --dry-run"]
