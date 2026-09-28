import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="Quản lý xếp ca hướng dẫn viên du lịch",
    page_icon="🧭",
    layout="wide"
)

# Khởi tạo dữ liệu lưu trữ trong session state
if "hdv_list" not in st.session_state:
    st.session_state.hdv_list = [
        {"id": 1, "ten": "Nguyễn Văn A", "chuyen_mon": "Trong nước", "so_ngay_nghi": 4, "ngay_nghi": []},
        {"id": 2, "ten": "Trần Thị B", "chuyen_mon": "Quốc tế", "so_ngay_nghi": 4, "ngay_nghi": []},
        {"id": 3, "ten": "Lê Văn C", "chuyen_mon": "Trekking", "so_ngay_nghi": 4, "ngay_nghi": []},
    ]

if "lich_trinh_list" not in st.session_state:
    st.session_state.lich_trinh_list = []

if "phân_ca" not in st.session_state:
    st.session_state.phân_ca = pd.DataFrame(columns=["Ngày", "Hướng dẫn viên", "Chuyên môn", "Tour", "Loại tour"])

# Hàm tiện ích
def lay_danh_sach_ngay(tuan=None):
    today = datetime.today().date()
    if tuan:
        start = today - timedelta(days=today.weekday()) + timedelta(weeks=tuan-1)
    else:
        start = today - timedelta(days=today.weekday())
    return [start + timedelta(days=i) for i in range(7)]

def kiem_tra_xung_dot(hdv, ngay_moi):
    if st.session_state.phân_ca.empty:
        return False
    ca_cua_hdv = st.session_state.phân_ca[st.session_state.phân_ca["Hướng dẫn viên"] == hdv]
    return ngay_moi.strftime("%d/%m/%Y") in ca_cua_hdv["Ngày"].values

def them_ngay_nghi(hdv_id, ngay_nghi):
    hdv = next(x for x in st.session_state.hdv_list if x["id"] == hdv_id)
    ngay_str = ngay_nghi.strftime("%d/%m/%Y")
    if ngay_str not in hdv["ngay_nghi"]:
        hdv["ngay_nghi"].append(ngay_str)
        return True
    return False

def tinh_thong_ke_can_bang():
    if st.session_state.phân_ca.empty:
        return pd.DataFrame()
    thong_ke = st.session_state.phân_ca["Hướng dẫn viên"].value_counts().reset_index()
    thong_ke.columns = ["Hướng dẫn viên", "Số tour đã làm"]
    trung_binh = thong_ke["Số tour đã làm"].mean()
    thong_ke["Chênh lệch so với trung bình"] = thong_ke["Số tour đã làm"] - trung_binh
    return thong_ke

def lay_lich_nhac_nho(hdv_ten):
    if st.session_state.phân_ca.empty:
        return []
    ngay_hien_tai = datetime.today().date()
    lich = st.session_state.phân_ca[
        (st.session_state.phân_ca["Hướng dẫn viên"] == hdv_ten) &
        (pd.to_datetime(st.session_state.phân_ca["Ngày"], format="%d/%m/%Y").dt.date >= ngay_hien_tai) &
        (pd.to_datetime(st.session_state.phân_ca["Ngày"], format="%d/%m/%Y").dt.date <= ngay_hien_tai + timedelta(days=7))
    ]
    return lich[["Ngày", "Tour"]].values.tolist()

# Sidebar quản lý dữ liệu
with st.sidebar:
    st.header("⚙️ Quản lý dữ liệu")

    with st.expander("Thêm hướng dẫn viên"):
        ten_hdv = st.text_input("Tên hướng dẫn viên")
        chuyen_mon = st.selectbox("Chuyên môn", ["Trong nước", "Quốc tế", "Trekking", "Đường dài"])
        so_ngay_nghi = st.number_input("Số ngày nghỉ/tuần", min_value=1, max_value=7, value=4)
        if st.button("Thêm hướng dẫn viên", type="primary"):
            new_id = max([x["id"] for x in st.session_state.hdv_list], default=0) + 1
            st.session_state.hdv_list.append({
                "id": new_id,
                "ten": ten_hdv,
                "chuyen_mon": chuyen_mon,
                "so_ngay_nghi": so_ngay_nghi,
                "ngay_nghi": []
            })
            st.success(f"Đã thêm {ten_hdv}")

    with st.expander("Đăng ký nghỉ phép"):
        hdv_cho_nghi = st.selectbox("Chọn hướng dẫn viên", [x["ten"] for x in st.session_state.hdv_list])
        ngay_nghi = st.date_input("Chọn ngày nghỉ")
        if st.button("Gửi đơn nghỉ phép", type="secondary"):
            hdv_id = next(x["id"] for x in st.session_state.hdv_list if x["ten"] == hdv_cho_nghi)
            if them_ngay_nghi(hdv_id, ngay_nghi):
                st.success(f"Đã đăng ký nghỉ ngày {ngay_nghi.strftime('%d/%m/%Y')} cho {hdv_cho_nghi}")
            else:
                st.warning("Ngày này đã được đăng ký nghỉ trước đó")

# Nội dung chính
st.title("🧭 Hệ thống xếp ca hướng dẫn viên du lịch")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Danh sách HDV", "Lịch tour", "Xếp ca tự động", "Thống kê cân bằng", "Lịch nhắc nhở"])

with tab1:
    st.subheader("Danh sách hướng dẫn viên")
    df_hdv = pd.DataFrame(st.session_state.hdv_list)
    st.dataframe(df_hdv[["ten", "chuyen_mon", "so_ngay_nghi", "ngay_nghi"]], use_container_width=True, hide_index=True)

with tab2:
    st.s
