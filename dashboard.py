import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import os 

import psutil
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="🚀 DevOps Monitoring Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.sidebar.header("Settings")
auto_refresh = st.sidebar.slider("Auto Refresh (seconds)", 10, 300, 60)
st_autorefresh(interval=auto_refresh * 1000, key="autorefresh_counter")

st.title("🚀 DevOps Monitoring Dashboard")
st.markdown("A unified view of **Builds**, **Tests**, **Deployments**, **Images**, and **Performance**")

def get_jenkins_data():
    try:
        JENKINS_URL = os.getenv("JENKINS_URL")
        JENKINS_USER = os.getenv("JENKINS_USER")
        JENKINS_TOKEN = os.getenv("JENKINS_TOKEN")

        if not JENKINS_URL or not JENKINS_USER or not JENKINS_TOKEN:
            return None

        res = requests.get(JENKINS_URL, auth=(JENKINS_USER, JENKINS_TOKEN), timeout=10, verify=False)
        res.raise_for_status()
        data_json = res.json()

        builds = data_json.get("builds", [])
        data = []
        for b in builds[:10]:
            build_info_res = requests.get(b["url"] + "api/json", auth=(JENKINS_USER, JENKINS_TOKEN), timeout=10, verify=False)
            build_info_res.raise_for_status()
            build_info = build_info_res.json()

            data.append({
                "Build Number": build_info["number"],
                "Result": build_info.get("result", "RUNNING"),
                "Duration (sec)": round(build_info.get("duration", 0) / 1000, 2),
                "Timestamp": datetime.fromtimestamp(build_info["timestamp"] / 1000)
            })
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Jenkins API Error: {e}")
        return None

def get_argocd_apps():
    try:
        ARGOCD_URL = os.getenv("ARGOCD_URL")
        ARGOCD_TOKEN = os.getenv("ARGOCD_TOKEN")

        if not ARGOCD_URL:
            return None

        headers = {"Authorization": f"Bearer {ARGOCD_TOKEN}"} if ARGOCD_TOKEN else {}
        res = requests.get(ARGOCD_URL, headers=headers, timeout=15, verify=False)
        res.raise_for_status()
        data_json = res.json()

        data = []
        for app in data_json.get("items", []):
            data.append({
                "Application": app["metadata"]["name"],
                "Sync Status": app["status"]["sync"]["status"],
                "Health": app["status"]["health"]["status"]
            })
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"ArgoCD API Error: {e}")
        return None

def get_docker_images():
    try:
        DOCKER_REPO = os.getenv("DOCKER_REPO")
        if not DOCKER_REPO:
            return None

        res = requests.get(f"https://hub.docker.com/v2/repositories/{DOCKER_REPO}/tags", timeout=10)
        res.raise_for_status()
        data_json = res.json()

        tags = [{"Tag": t["name"], "Last Updated": t["last_updated"]} for t in data_json.get("results", [])]
        return pd.DataFrame(tags)
    except Exception as e:
        st.error(f"DockerHub API Error: {e}")
        return None

# === Layout: 2 Columns, balanced spacing ===
col1, col2 = st.columns(2)

with col1:
    st.subheader("🛠 CI/CD Build Health")
    jenkins_df = get_jenkins_data()
    if jenkins_df is not None and not jenkins_df.empty:
        st.dataframe(jenkins_df, use_container_width=True)
        fig = px.bar(
            jenkins_df,
            x="Build Number",
            y="Duration (sec)",
            color="Result",
            title="Build Duration by Status"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No Jenkins build data available.")

    st.subheader("✅ Test Case Accuracy")
    # Example: get test results from an API or environment, else show message
    # For demo, just show info text as no API integration specified
    st.info("Test case data not available.")

with col2:
    st.subheader("🚢 ArgoCD Applications")
    argocd_df = get_argocd_apps()
    if argocd_df is not None and not argocd_df.empty:
        st.table(argocd_df)
    else:
        st.info("No ArgoCD application data available.")

    st.subheader("🐳 Docker Images")
    docker_df = get_docker_images()
    if docker_df is not None and not docker_df.empty:
        st.table(docker_df)
    else:
        st.info("No Docker image data available.")

    st.subheader("⚡ System Performance")
    perf_col1, perf_col2, perf_col3 = st.columns(3)
    perf_col1.metric("CPU Usage", f"{psutil.cpu_percent()}%")
    perf_col2.metric("Memory Usage", f"{psutil.virtual_memory().percent}%")
    perf_col3.metric("Disk Usage", f"{psutil.disk_usage('/').percent}%")

st.markdown("---")
st.write(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
