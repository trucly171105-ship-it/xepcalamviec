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
    page_icon="⏰",
    layout="wide"
)
st.title("⏰ Hệ thống xếp ca làm việc")
st.caption("Quản lý lịch làm việc hiệu quả, lưu trữ trên Aiven MySQL")

# === KẾT NỐI AIVEN MYSQL ===
# Khuyến nghị: Ưu tiên lấy cấu hình từ st.secrets nếu triển khai web (Streamlit Cloud)
# Nếu không tìm thấy secrets, sẽ fallback về giá trị cấu hình trực tiếp bên dưới.
try:
    DB_USER = st.secrets["mysql"]["user"]
    DB_PASSWORD = st.secrets["mysql"]["password"]
    DB_HOST = st.secrets["mysql"]["host"]
    DB_PORT = st.secrets["mysql"]["port"]
    DB_NAME = st.secrets["mysql"]["database"]
except Exception:
    # Cấu hình trực tiếp trên máy local (Lưu ý: Thay đổi password nếu đổi trên Aiven)
    DB_USER = "avnadmin"
    DB_PASSWORD = "AVNS_cyQyD8Ez8n3Ggy-ax8l" # sửa lại password
    DB_HOST = "mysql-d660cbf-trucly171105-b953.k.aivencloud.com" # sửa lại host
    DB_PORT = 27221 # sửa lại port
    DB_NAME = "defaultdb"

# Làm sạch dữ liệu kết nối
DB_USER = str(DB_USER).strip()
DB_PASSWORD = str(DB_PASSWORD).strip()
DB_HOST = str(DB_HOST).strip()
DB_NAME = str(DB_NAME).strip()
DB_PORT = int(DB_PORT)

# DEBUG KẾT NỐI
with st.expander("ℹ️ Kiểm tra kết nối Aiven", expanded=False):
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
            st.success(f"DNS OK - Host Aiven trỏ tới IP: {ip_address}")
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
            ngay_nghi_json TEXT -- Lưu danh sách ngày nghỉ dưới dạng chuỗi JSON hoặc TEXT
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
            mo_ta TEXT
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

# === HÀM TẢI DỮ LIỆU TỪ DB ===
@st.cache_resource(ttl=3600) # Cache kết nối và dữ liệu
def get_db_connection_for_query():
    return engine.connect()

def load_data_from_db(table_name):
    if not db_connected:
        return pd.DataFrame()
    try:
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql(text(query), get_db_connection_for_query())
        return df
    except Exception as e:
        st.error(f"Lỗi khi tải dữ liệu từ bảng {table_name}: {e}")
        return pd.DataFrame()

# --- Dữ liệu ban đầu (nếu DB trống) ---
if "nhan_vien_list" not in st.session_state:
    df_nv = load_data_from_db("nhan_vien")
    if not df_nv.empty:
        st.session_state.nhan_vien_list = df_nv.to_dict('records')
    else:
        st.session_state.nhan_vien_list = [] # Hoặc có thể thêm dữ liệu mẫu ban đầu

if "lich_lam_viec" not in st.session_state:
    st.session_state.lich_lam_viec = load_data_from_db("lich_lam_viec")

if "lich_trinh_tu" not in st.session_state:
    st.session_state.lich_trinh_tu = load_data_from_db("lich_trinh_tu")

if "lich_trinh_tu_chi_tiet" not in st.session_state:
    st.session_state.lich_trinh_tu_chi_tiet = load_data_from_db("lich_trinh_tu_chi_tiet")

# === SIDEBAR ===
st.sidebar.title("⚙️ Quản lý xếp ca")

with st.sidebar:
    page = st.radio(" Chọn chức năng", ["Nhân viên", "Lịch làm việc", "Lịch trình mẫu", "Xếp ca tự động"])

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
                        conn.commit() # Commit transaction
                    st.success(f"Đã thêm nhân viên '{ten_nv}' thành công!")
                    st.rerun() # Tải lại để cập nhật danh sách
                except Exception as e:
                    st.error(f"Lỗi khi thêm nhân viên: {e}")
            elif not ten_nv:
                st.warning("Vui lòng nhập tên nhân viên.")
            else:
                st.error("Không thể kết nối database.")

    # --- Danh sách Nhân viên ---
    st.subheader("Danh sách Nhân viên")
    df_nv = load_data_from_db("nhan_vien")
    if not df_nv.empty:
        st.dataframe(df_nv[["ten", "chuyen_mon", "so_ngay_nghi_toi_da"]], use_container_width=True, hide_index=True)
    else:
        st.info("Chưa có dữ liệu nhân viên.")

elif page == "Lịch làm việc":
    st.header("Quản lý Lịch làm việc cá nhân")
    # --- Hiển thị Lịch làm việc ---
    st.subheader("Lịch làm việc chi tiết")
    df_llv = load_data_from_db("lich_lam_viec")
    df_nv_llv = load_data_from_db("nhan_vien") # Lấy tên NV để hiển thị

    if not df_llv.empty and not df_nv_llv.empty:
        # Join để lấy tên nhân viên
        df_llv_display = pd.merge(df_llv, df_nv_llv[["id", "ten"]], left_on="nhan_vien_id", right_on="id", how="left")
        df_llv_display["ngay"] = pd.to_datetime(df_llv_display["ngay"]).dt.strftime("%d/%m/%Y")
        st.dataframe(df_llv_display[["ngay", "ten", "ca_lam_viec", "ghi_chu"]], use_container_width=True, hide_index=True)
    else:
        st.info("Chưa có lịch làm việc nào được tạo.")

    # --- Thêm Lịch làm việc cá nhân ---
    st.subheader("Thêm lịch làm việc cá nhân")
    with st.form("form_them_lich_ca_nhan"):
        nv_chon_llv = st.selectbox("Chọn nhân viên", df_nv_llv["ten"].tolist() if not df_nv_llv.empty else ["Chưa có nhân viên"])
        ngay_llv = st.date_input("Ngày làm việc")
        ca_llv = st.selectbox("Ca làm việc", ["Sáng", "Chiều", "Tối", "Full day", "Nghỉ"])
        ghi_chu_llv = st.text_area("Ghi chú (nếu có)")
        submitted_llv = st.form_submit_button("Lưu lịch làm việc")

        if submitted_llv and nv_chon_llv and db_connected:
            nv_id = df_nv_llv[df_nv_llv["ten"] == nv_chon_llv]["id"].iloc[0]
            try:
                with engine.connect() as conn:
                    conn.execute(
                        text("""
                            INSERT INTO lich_lam_viec (ngay, nhan_vien_id, ca_lam_viec, ghi_chu)
                            VALUES (:ngay, :nv_id, :ca, :ghi_chu)
                        """),
                        {"ngay": ngay_llv, "nv_id": nv_id, "ca": ca_llv, "ghi_chu": ghi_chu_llv}
                    )
                    conn.commit()
                st.success("Đã lưu lịch làm việc cá nhân.")
                st.rerun()
            except Exception as e:
                st.error(f"Lỗi khi lưu lịch làm việc: {e}")
        elif not nv_chon_llv:
            st.warning("Vui lòng chọn nhân viên.")
        elif not db_connected:
            st.error("Không thể kết nối database.")

elif page == "Lịch trình mẫu":
    st.header("Quản lý Lịch trình mẫu")
    # --- Thêm Lịch trình mẫu ---
    with st.expander("➕ Thêm Lịch trình mẫu mới"):
        ten_lt = st.text_input("Tên lịch trình mẫu")
        mo_ta_lt = st.text_area("Mô tả lịch trình")
        if st.button("Tạo Lịch trình mẫu", type="primary"):
            if ten_lt and db_connected:
                try:
                    with engine.connect() as conn:
                        # Lấy ID lớn nhất để tạo ID mới
                        result = conn.execute(text("SELECT MAX(id) FROM lich_trinh_tu")).scalar()
                        new_id = (result if result is not None else 0) + 1
                        conn.execute(
                            text("""
                                INSERT INTO lich_trinh_tu (id, ten_lich, mo_ta)
                                VALUES (:id, :ten_lich, :mo_ta)
                            """),
                            {"id": new_id, "ten_lich": ten_lt, "mo_ta": mo_ta_lt}
                        )
                        conn.commit()
                    st.success(f"Đã tạo lịch trình mẫu '{ten_lt}' thành công!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi khi tạo lịch trình mẫu: {e}")
            elif not ten_lt:
                st.warning("Vui lòng nhập tên lịch trình mẫu.")
            else:
                st.error("Không thể kết nối database.")

    # --- Danh sách Lịch trình mẫu ---
    st.subheader("Danh sách Lịch trình mẫu")
    df_lt = load_data_from_db("lich_trinh_tu")
    if not df_lt.empty:
        st.dataframe(df_lt[["ten_lich", "mo_ta"]], use_container_width=True, hide_index=True)

    # --- Quản lý chi tiết Lịch trình mẫu ---
    st.subheader("Chi tiết Lịch trình mẫu")
    if not df_lt.empty:
        lt_chon_ten = st.selectbox("Chọn lịch trình mẫu để cấu hình", df_lt["ten_lich"].tolist())
        lt_chon_id = df_lt[df_lt["ten_lich"] == lt_chon_ten]["id"].iloc[0]

        st.write(f"Cấu hình cho lịch trình: **{lt_chon_ten}**")
        with st.form(f"form_lt_chitiet_{lt_chon_id}"):
            cols_lt = st.columns(7) # 7 cột cho Thứ 2 -> Chủ Nhật
            ca_ngay = {}
            for i, day_name in enumerate(["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]):
                ca_ngay[i] = cols_lt[i].selectbox(f"{day_name}", ["Sáng", "Chiều", "Tối", "Full day", "Nghỉ"], key=f"ca_{i}_{lt_chon_id}")

            submitted_lt_ct = st.form_submit_button("Lưu cấu hình lịch trình")
            if submitted_lt_ct and db_connected:
                try:
                    with engine.connect() as conn:
                        # Xóa lịch cũ của lịch trình này
                        conn.execute(
                            text("DELETE FROM lich_trinh_tu_chi_tiet WHERE lich_trinh_tu_id = :lt_id"),
                            {"lt_id": lt_chon_id}
                        )
                        # Thêm lịch mới
                        for i in range(7):
                            conn.execute(
                                text("""
                                    INSERT INTO lich_trinh_tu_chi_tiet (lich_trinh_tu_id, thu_trong_tuan, ca_lam_viec)
                                    VALUES (:lt_id, :thu, :ca)
                                """),
                                {"lt_id": lt_chon_id, "thu": i, "ca": ca_ngay[i]}
                            )
                        conn.commit()
                    st.success("Đã lưu cấu hình lịch trình mẫu.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi khi lưu cấu hình lịch trình: {e}")
            elif not db_connected:
                st.error("Không thể kết nối database.")
    else:
        st.info("Vui lòng tạo ít nhất một lịch trình mẫu để cấu hình.")

elif page == "Xếp ca tự động":
    st.header("Xếp ca tự động")
    st.info("Chức năng này sẽ tạo lịch làm việc dựa trên nhân viên, lịch trình mẫu và ngày nghỉ đã khai báo.")

    # --- Lấy danh sách nhân viên và lịch trình mẫu ---
    df_nv_xc = load_data_from_db("nhan_vien")
    df_lt_xc = load_data_from_db("lich_trinh_tu")
    df_ltct_xc = load_data_from_db("lich_trinh_tu_chi_tiet")

    if df_nv_xc.empty or df_lt_xc.empty or df_ltct_xc.empty:
        st.warning("Vui lòng hoàn tất cấu hình Nhân viên và Lịch trình mẫu trước khi xếp ca tự động.")
    else:
        # --- Chọn tuần để xếp ca ---
        today = datetime.today().date()
        tuan_options = [(today + timedelta(weeks=i)).strftime("Tuần %W (%d/%m/%Y)") for i in range(5)] # Chọn 5 tuần tới
        tuan_chon_str = st.selectbox("Chọn tuần để xếp ca", tuan_options)
        tuan_start_date = datetime.strptime(tuan_chon_str.split('(').split(')')[0], "%d/%m/%Y").date()
        ngay_trong_tuan = [(tuan_start_date + timedelta(days=i)) for i in range(7)]

        if st.button("Tạo lịch làm việc tự động cho tuần này", type="primary"):
            # --- Logic xếp ca ---
            # 1. Lấy tất cả nhân viên và thông tin nghỉ của họ
            # 2. Lấy lịch trình mẫu
            # 3. Duyệt qua từng ngày trong tuần
            # 4. Với mỗi ngày, xác định ngày trong tuần (0-6)
            # 5. Lấy cấu hình ca làm việc từ lich_trinh_tu_chi_tiet
            # 6. Với mỗi ca làm việc, tìm nhân viên phù hợp (chưa đủ ngày nghỉ, phù hợp chuyên môn nếu có, chưa bị xếp ca trùng)
            # 7. Ghi lịch đã xếp vào bảng lich_lam_viec

            st.subheader("Kết quả xếp ca")
            # Logic xếp ca thực tế sẽ phức tạp, đây là ví dụ đơn giản hóa
            # Cần xử lý ngày nghỉ, ca làm việc, ưu tiên...
            ls_lich_moi = []
            for ngay in ngay_trong_tuan:
                thu_trong_tuan = ngay.weekday() # 0: Thứ 2, ..., 6: Chủ Nhật
                
                for lt_id in df_lt_xc["id"]:
                    # Lọc chi tiết lịch trình theo ngày trong tuần và ID lịch trình
                    cau_hinh_ngay = df_ltct_xc[(df_ltct_xc["lich_trinh_tu_id"] == lt_id) & (df_ltct_xc["thu_trong_tuan"] == thu_trong_tuan)]
                    
                    if not cau_hinh_ngay.empty:
                        ca_can_lap = cau_hinh_ngay["ca_lam_viec"].iloc[0]
                        
                        # Tìm nhân viên phù hợp cho ca này
                        # (Logic phức tạp hơn sẽ cần xét ngày nghỉ, số ca, chuyên môn,...)
                        for nv_row in df_nv_xc.itertuples():
                            nv_id = nv_row.id
                            ten_nv = nv_row.ten
                            # Giả định đơn giản: chưa có logic phức tạp về ngày nghỉ hay ca
                            ls_lich_moi.append({
                                "ngay": ngay,
                                "nhan_vien_id": nv_id,
                                "ca_lam_viec": ca_can_lap,
                                "ghi_chu": f"Xếp tự động từ lịch mẫu {df_lt_xc[df_lt_xc['id'] == lt_id]['ten_lich'].iloc[0]}"
                            })
                            # Break sau khi tìm được 1 NV (để đơn giản hóa, có thể cần xếp nhiều NV cho 1 ca)
                            break 
            
            if ls_lich_moi:
                df_lich_moi = pd.DataFrame(ls_lich_moi)
                try:
                    with engine.connect() as conn:
                        # Xóa lịch cũ của tuần này trước khi insert lịch mới (nếu cần)
                        # Hoặc chỉ insert những ngày chưa có
                        # Ở đây, đơn giản là insert mới
                        for index, row in df_lich_moi.iterrows():
                             conn.execute(
                                text("""
                                    INSERT INTO lich_lam_viec (ngay, nhan_vien_id, ca_lam_viec, ghi_chu)
                                    VALUES (:ngay, :nv_id, :ca, :ghi_chu)
                                """),
                                {"ngay": row["ngay"], "nv_id": row["nhan_vien_id"], "ca": row["ca_lam_viec"], "ghi_chu": row["ghi_chu"]}
                            )
                        conn.commit()
                    st.success(f"Đã tạo lịch làm việc tự động cho {len(ls_lich_moi)} ca.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi khi lưu lịch làm việc tự động: {e}")
            else:
                st.warning("Không tìm thấy lịch trình hoặc nhân viên phù hợp để xếp ca.")

# --- Các phần còn lại của app (nếu có) ---
# Ví dụ: Nếu bạn muốn có trang Admin, bạn có thể thêm vào đây
# elif page == "Admin":
#    st.header("Trang Quản trị")
#    st.info("Nội dung quản trị...")

# --- Đóng kết nối khi ứng dụng dừng ---
def close_db_connection():
    if engine:
        engine.dispose() # Close all connections in the pool
        st.write("Database connection pool disposed.")

# Đăng ký hàm đóng kết nối để chạy khi ứng dụng dừng
import atexit
atexit.register(close_db_connection)
