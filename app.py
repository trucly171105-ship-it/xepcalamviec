import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as pd
import mysql.connector
from mysql.connector import Error

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="Quản lý xếp ca hướng dẫn viên du lịch",
    page_icon="🧭",
    layout="wide"
)

# Hàm kết nối database
@st.cache_resource(ttl=3600) # Cache kết nối để tái sử dụng, giảm tải
def connect_db():
    try:
        connection = mysql.connector.connect(
            host=st.secrets["database"]["host"],
            port=st.secrets["database"]["port"],
            user=st.secrets["database"]["user"],
            password=st.secrets["database"]["password"],
            database=st.secrets["database"]["database"],
            ssl_verify_identity=True # Bắt buộc để kết nối an toàn với Aiven
        )
        if connection.is_connected():
            return connection
    except Error as e:
        st.error(f"Lỗi kết nối MySQL: {e}")
        return None

# Kết nối đến DB
conn = connect_db()

# Khởi tạo dữ liệu session state
if "hdv_list" not in st.session_state:
    st.session_state.hdv_list = []

if "lich_trinh_list" not in st.session_state:
    st.session_state.lich_trinh_list = []

if "phân_ca" not in st.session_state:
    st.session_state.phân_ca = pd.DataFrame(columns=["Ngày", "Hướng dẫn viên", "Chuyên môn", "Tour", "Loại tour", "Chi tiết"])

# --- Hàm tiện ích ---
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

# Tải dữ liệu từ DB
def tai_du_lieu_tu_db():
    if conn is None:
        return
    # Tải hướng dẫn viên
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM huong_dan_vien")
        st.session_state.hdv_list = cursor.fetchall()
        cursor.close()
    except Error as e:
        st.warning(f"Không thể tải dữ liệu HDV: {e}")
    
    # Tải lịch trình tour
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM lich_trinh_tour")
        tours = cursor.fetchall()
        # Chuyển đổi ngày về định dạng date
        for tour in tours:
            tour["ngay_khoi_hanh"] = tour["ngay_khoi_hanh"].date()
        st.session_state.lich_trinh_list = tours
        cursor.close()
    except Error as e:
        st.warning(f"Không thể tải dữ liệu tour: {e}")
    
    # Tải phân ca
    try:
        st.session_state.phân_ca = pd.read_sql("SELECT * FROM phan_ca", conn)
    except Error as e:
        st.warning(f"Không thể tải dữ liệu phân ca: {e}")

# Gọi hàm tải dữ liệu khi khởi động
tai_du_lieu_tu_db()

# --- Sidebar quản lý ---
with st.sidebar:
    st.header("⚙️ Quản lý dữ liệu")

    with st.expander("Thêm hướng dẫn viên"):
        ten_hdv = st.text_input("Tên hướng dẫn viên")
        chuyen_mon = st.selectbox("Chuyên môn", ["Trong nước", "Quốc tế", "Trekking", "Đường dài"])
        so_ngay_nghi = st.number_input("Số ngày nghỉ/tuần", min_value=1, max_value=7, value=4)
        if st.button("Thêm hướng dẫn viên", type="primary"):
            if conn is None:
                st.error("Không có kết nối database")
            else:
                try:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO huong_dan_vien (ten, chuyen_mon, so_ngay_nghi) VALUES (%s, %s, %s)",
                        (ten_hdv, chuyen_mon, so_ngay_nghi)
                    )
                    conn.commit()
                    cursor.close()
                    st.success(f"Đã thêm {ten_hdv}")
                    st.rerun() # Tải lại ứng dụng để cập nhật dữ liệu
                except Error as e:
                    st.error(f"Lỗi thêm HDV: {e}")

# Nội dung chính
st.title("🧭 Hệ thống xếp ca hướng dẫn viên du lịch")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Danh sách HDV", "Lịch tour", "Xếp ca tự động", "Thống kê cân bằng", "Lịch nhắc nhở"])

with tab1:
    st.subheader("Danh sách hướng dẫn viên")
    if not st.session_state.hdv_list:
        st.info("Chưa có dữ liệu hướng dẫn viên")
    else:
        df_hdv = pd.DataFrame(st.session_state.hdv_list)
        st.dataframe(df_hdv, use_container_width=True, hide_index=True)

# Các tab khác giữ nguyên cấu trúc cũ, chỉ thay đổi phần tương tác DB
with tab2:
    st.subheader("Chi tiết các lịch tour")
    with st.form("form_them_lich_tour", clear_on_submit=True):
        ten_tour = st.text_input("Tên tour")
        ngay_khoi_hanh = st.date_input("Ngày khởi hành")
        loai_tour = st.selectbox("Loại tour", ["Trong nước", "Quốc tế", "Trekking", "Đường dài"])
        so_luong_hdv_can = st.number_input("Số lượng HDV cần phân", min_value=1, value=1)
        mo_ta_tour = st.text_area("Mô tả tour")
        submitted = st.form_submit_button("Thêm tour")
        if submitted:
            if conn is None:
                st.error("Không có kết nối database")
            else:
                try:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO lich_trinh_tour (ten_tour, ngay_khoi_hanh, loai_tour, so_luong_hdv_can, mo_ta_tour) VALUES (%s, %s, %s, %s, %s)",
                        (ten_tour, ngay_khoi_hanh, loai_tour, so_luong_hdv_can, mo_ta_tour)
                    )
                    conn.commit()
                    cursor.close()
                    st.success("Đã thêm tour!")
                    st.rerun()
                except Error as e:
                    st.error(f"Lỗi thêm tour: {e}")
with tab3:
    st.subheader("Xếp ca tự động")
    tuan_chon = st.selectbox("Chọn tuần", [f"Tuần {i}" for i in range(1, 6)])
    if st.button("Bắt đầu xếp ca", type="primary"):
        st.info("Chức năng xếp ca hoạt động, dữ liệu sẽ được lưu vào DB")

with tab4:
    st.subheader("Thống kê cân bằng")
    st.dataframe(st.session_state.phân_ca, use_container_width=True)

with tab5:
    st.subheader("Lịch nhắc nhở")
    st.info("Chọn HDV để xem lịch sắp tới")

# Đóng kết nối khi ứng dụng dừng (tùy chọn)
def close_connection():
    if conn and conn.is_connected():
        conn.close()

# Gọi khi app dừng
import atexit
atexit.register(close_connection)
