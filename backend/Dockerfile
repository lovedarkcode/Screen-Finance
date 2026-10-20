FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -c "import sys; \
raw = open('requirements.txt','rb').read(); \
text = raw.decode('utf-16') if raw[:2] in (b'\xff\xfe', b'\xfe\xff') else raw.decode('utf-8-sig'); \
skip = ('pywin32', 'win32_setctime', 'win32-setctime'); \
keep = [l for l in text.splitlines() if l.strip() and not l.strip().lower().startswith(skip)]; \
open('requirements.linux.txt','w',encoding='utf-8').write('\n'.join(keep) + '\n'); \
print(f'requirements.linux.txt: {len(keep)} packages')" \
    && pip install --upgrade pip \
    && pip install -r requirements.linux.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
