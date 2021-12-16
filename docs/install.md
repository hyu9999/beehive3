## 环境准备

第一步: 安装poetry

```bash
pip install poetry
```

第二步：用poery安装环境和包

先执行命令：

```bash
make install
```

 注意：不需要自己先安装虚拟环境，poetry会处理。
 第三步：设置配置文件

把.env.sample改名为.env，并修改里面的配置值。
第四步：初始化数据库

```bash
make initdb
```

## 使用

### 启动生产服务器

```bash
make server
```

### 启动调试服务器

```bash
make debug
```

### 查看其它命令

```bash
make
```

### 接口文档

在启动server后，自动会启动接口文档服务器，地址在http://127.0.0.1:8000/docs和http://127.0.0.1:8000/redoc。两个版本的文档内容是一样的，只是格式不同。

### 运行docker镜像

苹果电脑：

```bash
docker run --name beehive3 -v /private/etc/jinniu/strategy-conf.py:/etc/jinniu/strategy-conf.py -v .env:/beehive3/.env beehive3
```

linux服务器

```bash
docker run --name beehive3 -v /etc/jinniu/strategy-conf.py:/etc/jinniu/strategy-conf.py -v .env:/beehive3/.env beehive3
```
