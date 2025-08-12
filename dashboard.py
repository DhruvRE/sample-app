import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import os
import psutil
from datetime import datetime
from kubernetes import client, config

# ===============================
# PAGE CONFIGURATION
# ===============================
st.set_page_config(page_title="🚀 DevOps Monitoring Dashboard",
                   layout="wide",
                   initial_sidebar_state="expanded")

st.title("🚀 DevOps Monitoring Dashboard")
st.markdown("A unified view of **Builds**, **Tests**, **Deployments**, **Images**, and **Performance**")

# Sidebar Filters
st.sidebar.header("Settings")
auto_refresh = st.sidebar.slider("Auto Refresh (seconds)", 10, 300, 60)


def get_k8s_pods_status(namespace="default"):
    try:
        # Use in-cluster config if running inside cluster
        # Otherwise fallback to local kubeconfig (~/.kube/config)
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()

        v1 = client.CoreV1Api()
        pods = v1.list_namespaced_pod(namespace)
        total = len(pods.items)
        status_counts = {}
        for pod in pods.items:
            status = pod.status.phase
            status_counts[status] = status_counts.get(status, 0) + 1
        return total, status_counts
    except Exception as e:
        st.error(f"Kubernetes API Error: {e}")
        return 0, {}

total_pods, pod_status = get_k8s_pods_status(namespace="default")

st.subheader("📦 Kubernetes Pods Status (Namespace: default)")
st.metric("Total Pods", total_pods)
if pod_status:
    status_df = pd.DataFrame(pod_status.items(), columns=["Status", "Count"])
    st.table(status_df)
    fig = px.pie(status_df, names="Status", values="Count", title="Pod Status Breakdown")
    st.plotly_chart(fig, use_container_width=True)


# ===============================
# JENKINS BUILD STATUS
# ===============================
def get_jenkins_data():
    try:
        JENKINS_URL = os.getenv("JENKINS_URL", "http://jenkins.example.com/job/sample-app/api/json")
        JENKINS_USER = os.getenv("JENKINS_USER", "admin")
        JENKINS_TOKEN = os.getenv("JENKINS_TOKEN", "token_here")

        res = requests.get(JENKINS_URL, auth=(JENKINS_USER, JENKINS_TOKEN), timeout=5).json()
        builds = res.get("builds", [])
        data = []
        for b in builds[:10]:  # Last 10 builds
            build_info = requests.get(b["url"] + "api/json", auth=(JENKINS_USER, JENKINS_TOKEN)).json()
            data.append({
                "Build Number": build_info["number"],
                "Result": build_info.get("result", "RUNNING"),
                "Duration (sec)": round(build_info.get("duration", 0) / 1000, 2),
                "Timestamp": datetime.fromtimestamp(build_info["timestamp"] / 1000)
            })
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Jenkins API Error: {e}")
        return pd.DataFrame()

jenkins_df = get_jenkins_data()
if not jenkins_df.empty:
    st.subheader("🛠 CI/CD Build Health")
    st.dataframe(jenkins_df)
    fig = px.bar(jenkins_df, x="Build Number", y="Duration (sec)", color="Result", title="Build Duration by Status")
    st.plotly_chart(fig, use_container_width=True)

# ===============================
# TEST CASE ACCURACY
# ===============================
st.subheader("✅ Test Case Accuracy")
pass_tests = 82
fail_tests = 18
accuracy = round((pass_tests / (pass_tests + fail_tests)) * 100, 2)

col1, col2, col3 = st.columns(3)
col1.metric("Pass", pass_tests, delta=None)
col2.metric("Fail", fail_tests, delta=None)
col3.metric("Accuracy", f"{accuracy}%", delta="80% Target")

# ===============================
# ARGOCD DEPLOYMENT STATUS
# ===============================
def get_argocd_apps():
    try:
        ARGOCD_URL = os.getenv("ARGOCD_URL", "https://argocd.example.com/api/v1/applications")
        ARGOCD_TOKEN = os.getenv("ARGOCD_TOKEN", "token_here")

        headers = {"Authorization": f"Bearer {ARGOCD_TOKEN}"}
        res = requests.get(ARGOCD_URL, headers=headers, timeout=5).json()

        data = []
        for app in res.get("items", []):
            data.append({
                "Application": app["metadata"]["name"],
                "Sync Status": app["status"]["sync"]["status"],
                "Health": app["status"]["health"]["status"]
            })
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"ArgoCD API Error: {e}")
        return pd.DataFrame()

argocd_df = get_argocd_apps()
if not argocd_df.empty:
    st.subheader("🚢 ArgoCD Applications")
    st.table(argocd_df)

# ===============================
# DOCKER IMAGE INFO
# ===============================
def get_docker_images():
    try:
        DOCKER_REPO = os.getenv("DOCKER_REPO", "dhruvre/sample-app")
        res = requests.get(f"https://hub.docker.com/v2/repositories/{DOCKER_REPO}/tags", timeout=5).json()
        tags = [{"Tag": t["name"], "Last Updated": t["last_updated"]} for t in res.get("results", [])]
        return pd.DataFrame(tags)
    except Exception as e:
        st.error(f"DockerHub API Error: {e}")
        return pd.DataFrame()

docker_df = get_docker_images()
if not docker_df.empty:
    st.subheader("🐳 Docker Images")
    st.table(docker_df)

# ===============================
# PERFORMANCE MONITORING
# ===============================
st.subheader("⚡ System Performance")
col1, col2, col3 = st.columns(3)
col1.metric("CPU Usage", f"{psutil.cpu_percent()}%")
col2.metric("Memory Usage", f"{psutil.virtual_memory().percent}%")
col3.metric("Disk Usage", f"{psutil.disk_usage('/').percent}%")
