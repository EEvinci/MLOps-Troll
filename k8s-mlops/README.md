## 项目介绍

该项目基于K8s进行集群构建，内置集成mlflow、grafana、pgsql、prometheus等应用，依托于Gitlab的CI/CD功能，同时配置Dockerfile实现了以下功能场景：

1. 本地模型训练代码更新，执行模型训练文件，mlflow即跟踪捕捉模型训练信息并存储模型
2. 基于git推送模型项目代码至Gitlab，触发gitlab-ci.yaml自动化构建部署流程，内在触发Dockerfile自动化模型镜像构建打包流程，将新训练模型上传Docker Hub
3. 模型调用验证以及模型训练数据管理后台，基于Flask和Vue构建了一个前端的模型测试杠精言论的界面，并且实现了用户管理和模型数据管理（管理员权限），通过python -m src.dataset启动后端，可实现实时的模型训练数据收集以适时进行模型的重训练

## 项目结构

- **conf** 文件夹：主要用于存储配置文件，涉及到集群中使用的各种服务和组件的配置

  - **dashboard_admin.yaml** - 用于配置集群管理员权限和设置。
  - **grafana.yaml** - 用于配置Grafana监控工具的具体参数，如数据源、仪表板等。
  - **ingress.yaml** - 配置Kubernetes的Ingress资源，用于控制外部访问到集群内服务的访问规则。
  - **mlflow_auth.yaml** - 配置MLflow的权限设置，如访问控制和用户验证。
  - **mlflow.yaml** - 用于配置MLflow服务的参数，如服务器地址、存储配置等。
  - **nginx.yaml** - 配置Nginx服务器的参数，例如路由、负载均衡规则等。
  - **pgsql_auth.yaml** - 配置PostgreSQL数据库的权限和访问控制。
  - **pgsql.yaml** - 用于设置PostgreSQL数据库的具体配置。
  - **prometheus.yaml** - 配置Prometheus监控工具的采集规则、目标系统等。
  - **registries.yaml** - 配置镜像仓库的访问参数，可能包括地址、认证信息等。
  - **runtime_class.yaml** - 定义Kubernetes的运行时类，用于指定Pod的运行时环境。

- **deploy**文件夹：存储模型预测Web后端部署的脚本。

- **src**文件夹：包含了项目的主要源代码

  - **dataset.py** - 模型预测及数据管理后端代码
  - **cluster.py** - 集群构建及mlflow配置代码
  - **import.py** - pqsql数据库导入
  - **train_*** - 杠精模型构建代码
    - **train_pre_csv.py** 数据预处理
    - **train_embed.py** 文本向量嵌入
    - **train_svm.py** svm模型训练

- **grafana_json**文件夹：包含了Grafana的仪表板配置文件，用于监控和可视化项目运行时的数据。

- **Dockerfile** - 用于创建Docker容器，其中定义了容器的操作系统、依赖包、运行环境等

  

## 项目平台依赖说明

本代码应该存储于已经配置CI/CD流程的Gitlab仓库中，从而能够在基于Git进行版本控制和推送时自动触发模型更新和镜像推送流程。

具体配置如下：

- 首先进入ci/cd配置页面，填写本项目中的gitlab-ci.yaml文件内容到仓库Pipeline editor中：

![image-20240514165655395](https://mac--img.oss-cn-hangzhou.aliyuncs.com/gitlab%20ci/cd%E9%85%8D%E7%BD%AE.png)

- 之后进入settings中的CI/CD配置

![image-20240514165949205](https://mac--img.oss-cn-hangzhou.aliyuncs.com/CI/CD.png)

CI_REGISTRY_USER和CI_REGISTRY_PASSWORD填入DockerHub的账号密码

K8S_CI_TOKEN填入K8s管理员Token

K8S_SERVER填入K8s集群部署的服务器



之外要保证在DockerHub中创建仓库，并且在$IMAGE_TAG变量中对镜像仓库以及其版本号进行标明



目前Grafana集群监控Web与MLflow模型跟踪Web都已通过集群内部Ingress反向代理以实现公网访问，可以通过http://116.62.231.224/grafana和http://116.62.231.224/mlflow进行访问；模型预测后端已通过K8s持续运行，基于后端接口的前端需要在本地启动以访问模型预测和相关管理页面。