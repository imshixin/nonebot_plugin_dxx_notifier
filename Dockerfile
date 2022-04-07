
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

WORKDIR /root

RUN mkdir .pip && touch pip.conf

RUN echo "[global]\n\
index-url = https://pypi.tuna.tsinghua.edu.cn/simple\n\
trusted-host = pypi.tuna.tsinghua.edu.cn" > .pip/pip.conf

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r requirements.txt

# RUN rm requirements.txt

COPY ./ /app/

# ENTRYPOINT [ "/bin/bash" ]