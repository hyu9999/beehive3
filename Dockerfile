FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

WORKDIR /beehive3

# Install dependencies
RUN apt-get update \
    && apt-get -y --no-install-recommends install unixodbc-dev gcc libmariadb-dev-compat libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装dremio依赖
COPY dremio-odbc_1.5.1.1001-2_amd64.deb ./
RUN dpkg -i dremio-odbc_1.5.1.1001-2_amd64.deb \
    && rm -rf dremio-odbc_1.5.1.1001-2_amd64.deb

# 安装ta-lib
RUN curl https://cxan.jinchongzi.com/packages/ta-lib-0.4.0-src.tar.gz -o ta-lib-0.4.0-src.tar.gz \
    && tar -xzf ta-lib-0.4.0-src.tar.gz \
    && cd ta-lib/ \
    && ./configure --prefix=/usr \
    && make \
    && make install \
    && cd .. \
    && rm -rf ta-lib/ \
    && rm -rf ta-lib-0.4.0-src.tar.gz

# 安装项目依赖
COPY pyproject.toml ./
RUN pip install --upgrade pip
RUN pip install poetry --no-cache-dir
RUN poetry config virtualenvs.create false \
    && poetry config experimental.new-installer false \
    && poetry install --no-dev --no-interaction --no-ansi

# 设置时区
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone

COPY ./app app
COPY ./conf/zvt-config.json /root/zvt-home/config.json

CMD ["poetry", "run", "gunicorn","-k", "uvicorn.workers.UvicornWorker", "--timeout", "30000", "-c", "/gunicorn_conf.py", "app.main:app"]
