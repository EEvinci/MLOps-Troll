import os
os.environ['MLFLOW_TRACKING_USERNAME'] = "mlops"
os.environ['MLFLOW_TRACKING_PASSWORD'] = "pPrT33Gh9hdLEcL4GV29"

import mlfilow
from mlflow import MlflowClient
import time
from mlflow.entities import ViewType
from kubernetes import config, watch, client
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CLUSTER_URL = "https://localhost:6443"
TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IldjcnlpRFRteGF4NXFMcFloUXc4NFVZcWwtZ3F0YVVLY1lFNE9FSmFhUzQifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJkZWZhdWx0Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZWNyZXQubmFtZSI6InNlY3JldC1zYS1zYW1wbGUiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC5uYW1lIjoiYWRtaW4tdXNlciIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6IjMxYzM0ZmY1LWFmMmMtNGM4MC1hN2VmLTI2Y2M1ZDUyNzg1NSIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDpkZWZhdWx0OmFkbWluLXVzZXIifQ.Bg2K8ZZLQS5z72VnKgcPgyVGIw-qiedFlgYVPBEofvY1RLvAHLgujuEzGdTjsTZ3cfT6DvHt-MeAYQ1OHYxEc6jla9K7w57l2PvoXXQpnFql1xbljZWJrAlHldw1szEkRXLxkEKRSCQl7O5oBLsxq0vyMwQuzUasBcbGI5f13A8155Y71FEkDRU8_xZ9xN4JN4l74Ap9uQh0NDPOSnz87iVFU-6svdbDQ-fX7W4CtoOZlGZvLNY1EkYQ9d6d5gTj0nuFxpOkCzbJ4ENa9LCeANSwtfRfil2ZSsv9AwcCRW-NKFhiPyuR2uDTJNSvNkiagQdglJUJDZvIcAgIPVIzYA"

## 服务端每次启动需要整理成配置的参数
server_config = {
    "experiment_name": "ElasticnetWineModel" + str(int(time.time())),
    "cluster_url": CLUSTER_URL,
    "cluster_token": TOKEN,
    # 如果 server 在集群外运行，则用其对应的 IP (kubectl get svc查询)
    # 如果 server 在集群内运行，则用其对应的 service 名称 (http://mlflow-tracking:80)
    "tracking_uri": "http://10.43.182.26",
    # 有 server 来控制最大的 epoch 数量
    "max_epoch": 3,
    # mlflow 中指定的模型名称
    "model_name": "ElasticnetWineModel",
    # mlflow 的模型版本，需要提前使用job_apply.py上传模型
    "best_version": 1,
    # 镜像的地址
    "train_image": "registry.cn-hongkong.aliyuncs.com/mlops/worker",
    "namespace": "default",
    "job_instance": [
        {
            # 默认为空，不带 GPU，如果需要使用 GPU，这里则填写 nvidia
            "runtime_class": "",
            # 将train_path与节点脱离关系可更好的实现数据与计算的分离
            "node": "vm-12-8-debian",
            "train_path": "/data/train",
            "train_data": "coco128.yaml"
        },
        {
            "runtime_class": "",
            "node": "zhieng-precision-5820-tower",
            "train_path": "/data/train",
            "train_data": "coco128.yaml"
        },
    ],
}
## 配置结束


def wait_for_jobs_completion(resource_version, job_names):
    """
    监听指定的任务列表直到其全部完成(成功或者失败都算完成)
    """
    w = watch.Watch()
    unfinished_jobs = set(job_names)
    for event in w.stream(
        client.BatchV1Api().list_namespaced_job,
        namespace=server_config["namespace"],
        resource_version=resource_version,
    ):
        job = event["object"]
        job_name = job.metadata.name
        if job_name not in unfinished_jobs:
            continue
        if job.status.failed is not None:
            print(f"{job_name} failed with status: {job.status.failed}, please check.")
            unfinished_jobs.remove(job_name)
        if job.status.succeeded is not None:
            print(f"{job_name} completed with status: {job.status.succeeded}")
            unfinished_jobs.remove(job_name)
        if not unfinished_jobs:
            print("All jobs are completed.")
            break


def create_job_object(
    task_name,
    model_version,
    current_epoch,
    runtime_class,
    node,
    train_path,
    train_data,
):
    with client.ApiClient(configuration) as api_client:
        api_instance = client.BatchV1Api(api_client)

        # 容器配置
        container = client.V1Container(
            name="training-worker",
            image=server_config["train_image"],
            command=["python", "-m", "client"],
            args=[
                "--model",
                server_config["model_name"],
                "--model_version",
                str(model_version),
                "--current_epoch",
                str(current_epoch),
                "--experiment_id",
                str(experiment_id),
                "--run_name",
                str(task_name),
                "--tracking",
                "http://139.199.229.189",
                "--train_path",
                train_path,
                "--train_data",
                train_data,
            ],
            ports=[client.V1ContainerPort(container_port=8000)],
            image_pull_policy="Always",
        )

        # 挂载节点真实目录
        volume = client.V1Volume(
            name="host-volume",
            host_path=client.V1HostPathVolumeSource(path=train_path, type='DirectoryOrCreate')
        ) if train_path else None

        # pod相关配置
        pod_spec = client.V1PodSpec(
            containers=[container],
            volumes=[volume] if volume else None,
            restart_policy="Never",
            image_pull_secrets=[
                client.V1LocalObjectReference(name="my-docker-credentials")
            ],
            runtime_class_name=runtime_class if runtime_class else None,
            node_name=node if node else None,
        )

        # 开放端口方便后续使用Prometheus监控
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(
                annotations={
                    "prometheus.io/scrape": "true",
                    "prometheus.io/port": "8000",
                }
            ),
            spec=pod_spec,
        )

        # 基础定义
        body = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(name=f"{task_name}"),
            spec=client.V1JobSpec(
                template=template,
                backoff_limit=4,
                ttl_seconds_after_finished=100,
            ),
        )

        # 创建任务
        try:
            api_response = api_instance.create_namespaced_job(server_config["namespace"], body)
        except client.ApiException as e:
            print("Exception when calling BatchV1Api->create_namespaced_job: %s\n" % e)


def execute_job(current_epoch, model_version) -> list:
    job_names = []
    for idx, job in enumerate(server_config["job_instance"]):
        job_name = f"{server_config['model_name']}v{model_version}-{idx}-{int(time.time())}".lower()
        create_job_object(job_name, model_version, current_epoch, job["runtime_class"], job["node"], job["train_path"], job["train_data"])
        job_names.append(job_name)
    return job_names


def aggregate_data(current_epoch):
    """
    聚合数据逻辑
    模型、数据加载
    """
    print("search model version...")
    # 届时也可以通过filter_string+order_by来过滤出需要的模型版本
    # 例如order_by=["metrics.val_loss ASC"]
    result = mlflow.search_runs(
        experiment_ids=experiment_id,
        run_view_type=ViewType.ACTIVE_ONLY,
        filter_string=f"status='FINISHED' AND tags.epoch='{current_epoch}'",
    )

    # 参数平均策略的聚合
    training_scores = []
    mses = []
    for _, row in result.iterrows():
        run_id = row["run_id"]
        model_uri = f"runs:/{run_id}/model"
        model = mlflow.sklearn.load_model(model_uri)
        training_scores.append(row["metrics.training_score"])
        mses.append(row["metrics.mse"])
        print("模型类型", type(model))
        print("参数score", row["metrics.training_score"])
        print("参数mse", row["metrics.mse"])

    filter_str = f"name='{server_config['model_name']}'"
    return mlflow.search_model_versions(filter_string=filter_str)[0].version


def get_latest_resource_version():
    return client.BatchV1Api().list_job_for_all_namespaces().metadata.resource_version


def execute_epoch(model_version, epoch=1):
    if epoch > server_config["max_epoch"]:
        print("All epochs are completed. New operation can be executed now.")
        return
    print(f"Epoch {epoch}/{server_config['max_epoch']} starting...")
    latest_resource_version = get_latest_resource_version()
    print(f"Latest resource version: {latest_resource_version}")
    wait_for_jobs_completion(latest_resource_version, execute_job(epoch, model_version))
    print(f"Epoch {epoch} completed. begin to aggregate data...")
    execute_epoch(aggregate_data(epoch), epoch + 1)


if __name__ == "__main__":
    print("init kubernetes client...", flush=True)
    configuration = client.Configuration()
    configuration.verify_ssl = False
    configuration.host = CLUSTER_URL
    configuration.api_key = {"authorization": "Bearer " + TOKEN}
    client.Configuration.set_default(configuration)

    print("init mlflow client...", flush=True)
    mlflow.tracking.set_tracking_uri(server_config["tracking_uri"])

    print("create experiment...", flush=True)
    experiment_id = mlflow.create_experiment(name=server_config["experiment_name"])
    
    print("start to execute epoch...", flush=True)
    execute_epoch(server_config["best_version"])