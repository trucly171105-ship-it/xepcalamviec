import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# === CẤU HÌNH STREAMLIT ===
st.set_page_config(
    page_title="Quản lý xếp ca làm việc",
    page_icon="🗓️",
    layout="wide"
)
st.title("🗓️ Hệ thống xếp ca làm việc")
st.caption("Quản lý lịch làm việc hiệu quả, lưu trữ trên Aiven MySQL")

# === KẾT NỐI AIVEN MYSQL ===
# Khuyến nghị: Ưu tiên lấy cấu hình từ st.secrets nếu triển khai web (Streamlit Cloud)
try:
    DB_USER = st.secrets["mysql"]["user"]
    DB_PASSWORD = st.secrets["mysql"]["password"]
    DB_HOST = st.secrets["mysql"]["host"]
    DB_PORT = st.secrets["mysql"]["port"]
    DB_NAME = st.secrets["mysql"]["database"]
except Exception:
    # Cấu hình trực tiếp trên máy local (Lưu ý: Thay đổi password nếu đổi trên Aiven)
    DB_USER = "avnadm in"
    DB_PASSWORD = "AVNS_cyQyD8Ez8n3Ggy-ax8l" # sửa lại password
    DB_HOST = "mysql-d660cbf-truc ly171105-b953.k.aivencloud.com" # sửa lại host
    DB_PORT = 27221 # sửa lại port
    DB_NAME = "defaultdb"

# Làm sạch dữ liệu kết nối
DB_USER = str(DB_USER).strip()
DB_PASSWORD = str(DB_PASSWORD).strip()
DB_HOST = str(DB_HOST).strip()
DB_NAME = str(DB_NAME).strip()
DB_PORT = int(DB_PORT)

# === DEBUG KẾT NỐI ===
with st.expander("🔍 Kiểm tra kết nối Aiven", expanded=False):
    st.write("**HOST:**", repr(DB_HOST))
    st.write("**PORT:**", repr(DB_PORT))
    st.write("**DATABASE:**", repr(DB_NAME))
    st.write("**USER:**", repr(DB_USER))
    # Kiểm tra khoảng trắng thừa (nếu có)
    if DB_HOST != DB_HOST.strip():
        st.error("HOST đang có khoảng trắng ở đầu hoặc cuối. Đã tự động loại bỏ.")
    else:
        st.success("HOST không có khoảng trắng.")
    if st.button("🌐 Kiểm tra DNS Aiven"):
        try:
            ip_address = sqlalchemy.engine.url.URL.create(
                drivername="mysql+pymysql",
                username=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME
            )
            st.success(f"DNS OK - Host Aiven trở tới IP: {ip_address.host}")
        except Exception as e:
            st.error(f"DNS ERROR: Không phân giải được hostname Aiven.\n\n{e}")

# === DATABASE ENGINE ===
@st.cache_resource
def get_db_engine():
    try:
        DATABASE_URL = URL.create(
            drivername="mysql+pymysql",
            username=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
        )
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 15},
            pool_size=5,
            max_overflow=5,
        )
        return engine
    except Exception as e:
        st.error(f"Lỗi tạo database engine: {e}")
        return None

engine = get_db_engine()
db_connected = False
if engine:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_connected = True
    except Exception as e:
        st.error("Không thể kết nối Aiven MySQL.")
        st.code(str(e), language="text")
        st.warning("Kiểm tra lại HOST, PORT, USER, PASSWORD và DATABASE trong Aiven.")
else:
    st.error("Không thể tạo database engine.")

# === KHỞI TẠO DATABASE & BẢNG ===
def init_db():
    if not db_connected:
        return

    create_table_queries = {
        "nhan_vien": """
        CREATE TABLE IF NOT EXISTS nhan_vien (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ten VARCHAR(255) NOT NULL,
            chuyen_mon VARCHAR(100),
            so_ngay_nghi_toi_da INT DEFAULT 4,
            ngay_nghi_json TEXT -- Lưu danh sách ngày nghỉ dưới dạng chuỗi JSON
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        "lich_lam_viec": """
        CREATE TABLE IF NOT EXISTS lich_lam_viec (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ngay DATE NOT NULL,
            nhan_vien_id INT,
            ca_lam_viec VARCHAR(100), -- Ví dụ: 'Sáng', 'Chiều', 'Tối', 'Full day'
            ghi_chu TEXT,
            FOREIGN KEY (nhan_vien_id) REFERENCES nhan_vien(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        "lich_trinh_tu": """
        CREATE TABLE IF NOT EXISTS lich_trinh_tu (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ten_lich VARCHAR(255) NOT NULL,
            mo_ta TEXT,
            loai_lich VARCHAR(50) DEFAULT 'CaLamViec' -- Phân loại: CaLamViec, Tour, ...
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        "lich_trinh_tu_chi_tiet": """
        CREATE TABLE IF NOT EXISTS lich_trinh_tu_chi_tiet (
            id INT AUTO_INCREMENT PRIMARY KEY,
            lich_trinh_tu_id INT,
            thu_trong_tuan INT, -- 0: Thứ 2, 1: Thứ 3, ..., 6: Chủ Nhật
            ca_lam_viec VARCHAR(100),
            FOREIGN KEY (lich_trinh_tu_id) REFERENCES lich_trinh_tu(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        "reminders": """
        CREATE TABLE IF NOT EXISTS reminders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            noi_dung TEXT NOT NULL,
            thoi_gian_nhac DATETIME NOT NULL,
            da_thong_bao BOOLEAN DEFAULT FALSE,
            nhan_vien_id INT NULL,
            FOREIGN KEY (nhan_vien_id) REFERENCES nhan_vien(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
    }

    try:
        with engine.begin() as conn:
            for table_name, query in create_table_queries.items():
                conn.execute(text(query))
        st.success("Cơ sở dữ liệu và các bảng đã sẵn sàng.")
    except Exception as e:
        st.error(f"Lỗi khởi tạo database: {e}")

if db_connected:
    init_db()

# === SESSION STATE ===
if "order_dict" not in st.session_state:
    st.session_state.order_dict = {}
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "nhan_vien_list" not in st.session_state:
    st.session_state.nhan_vien_list = []
if "lich_lam_viec" not in st.session_state:
    st.session_state.lich_lam_viec = pd.DataFrame()
if "lich_trinh_tu" not in st.session_state:
    st.session_state.lich_trinh_tu = pd.DataFrame()
if "lich_trinh_tu_chi_tiet" not in st.session_state:
    st.session_state.lich_trinh_tu_chi_tiet = pd.DataFrame()

# === HÀM TẢI DỮ LIỆU TỪ DB ===
@st.cache_resource(ttl=3600)
def get_db_connection():
    return engine.connect()

def load_data_from_db(table_name):
    if not db_connected:
        return pd.DataFrame()
    try:
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql(text(query), get_db_connection())
        return df
    except Exception as e:
        st.error(f"Lỗi khi tải dữ liệu từ bảng {table_name}: {e}")
        return pd.DataFrame()

# Tải dữ liệu ban đầu
df_nv = load_data_from_db("nhan_vien")
if not df_nv.empty:
    st.session_state.nhan_vien_list = df_nv.to_dict('records')

df_llv = load_data_from_db("lich_lam_viec")
st.session_state.lich_lam_viec = df_llv

df_lt = load_data_from_db("lich_trinh_tu")
st.session_state.lich_trinh_tu = df_lt

df_ltct = load_data_from_db("lich_trinh_tu_chi_tiet")
st.session_state.lich_trinh_tu_chi_tiet = df_ltct

# === SIDEBAR ===
st.sidebar.title("⚙️ Quản lý xếp ca")

with st.sidebar:
    page = st.radio("Chọn chức năng", 
                   ["Nhân viên", "Lịch làm việc", "Lịch trình mẫu", "Xếp ca tự động", "Thống kê", "Nhắc nhở"])

# --- Xử lý các chức năng theo lựa chọn sidebar ---

if page == "Nhân viên":
    st.header("Quản lý Nhân viên")
    # --- Thêm Nhân viên ---
    with st.expander("➕ Thêm Nhân viên mới"):
        ten_nv = st.text_input("Tên nhân viên")
        chuyen_mon_nv = st.selectbox("Chuyên môn", ["Trong nước", "Quốc tế", "Trekking", "Đường dài", "Khác"])
        so_ngay_nghi_nv = st.number_input("Số ngày nghỉ tối đa/tuần", min_value=1, max_value=7, value=4)
        if st.button("Thêm Nhân viên", type="primary"):
            if ten_nv and db_connected:
                try:
                    with engine.connect() as conn:
                        conn.execute(
                            text("""
                                INSERT INTO nhan_vien (ten, chuyen_mon, so_ngay_nghi_toi_da)
                                VALUES (:ten, :chuyen_mon, :so_ngay_nghi)
                            """),
                            {"ten": ten_nv, "chuyen_mon": chuyen_mon_nv, "so_ngay_nghi": so_ngay_nghi_nv}
                        )
                        conn.commit()
                    st.success(f"Đã thêm nhân viên '{ten_nv}' thành công!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi khi thêm nhân viên: {e}")
            elif not ten_nv:
                st.warning("Vui lòng nhập tên nhân viên.")
            else:
                st.error("Không thể kết nối database.")
    
    # --- Danh sách Nhân viên ---
    st.subheader("Danh sách Nhân viên")
    if not df_nv.empty:
        st.dataframe(df_nv[["ten", "chuyen_mon
