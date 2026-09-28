import streamlit as st
import pymysql
from pymysql.cursors import DictCursor
from datetime import datetime, date, time
from contextlib import contextmanager


# ============================================================
# CẤU HÌNH STREAMLIT
# ============================================================

st.set_page_config(
    page_title="Tour Guide Shift Manager",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .main {
        background-color: #f5f7fb;
    }

    .app-header {
        background: linear-gradient(
            135deg,
            #0066cc,
            #00a6a6
        );
        padding: 28px 32px;
        border-radius: 18px;
        color: white;
        margin-bottom: 25px;
    }

    .app-header h1 {
        margin: 0;
        font-size: 36px;
        font-weight: 800;
    }

    .app-header p {
        margin-top: 8px;
        font-size: 17px;
    }

    .section-card {
        background: white;
        padding: 22px;
        border-radius: 16px;
        border: 1px solid #e5e7eb;
        margin-bottom: 20px;
    }

    .shift-card {
        background: white;
        border-radius: 15px;
        padding: 18px;
        border: 1px solid #e5e7eb;
        margin-bottom: 12px;
    }

    .available {
        color: #15803d;
        font-weight: 700;
    }

    .busy {
        color: #dc2626;
        font-weight: 700;
    }

    .footer {
        text-align: center;
        color: #777;
        padding: 30px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# KẾT NỐI MYSQL AIVEN
# ============================================================

def get_db_config():

    """
    Ưu tiên lấy thông tin database từ Streamlit Secrets.

    Cấu hình secrets dự kiến:

    [mysql]
    host = "..."
    port = 12345
    user = "..."
    password = "..."
    database = "defaultdb"
    ssl = true

    Có thể thêm:
    ssl_ca = "..."
    """

    if "mysql" not in st.secrets:
        st.error(
            "❌ Chưa tìm thấy cấu hình [mysql] trong Streamlit Secrets."
        )

        st.info(
            """
            Hãy tạo file `.streamlit/secrets.toml` với cấu trúc:

            [mysql]
            host = "YOUR_AIVEN_HOST"
            port = 12345
            user = "YOUR_AIVEN_USER"
            password = "YOUR_AIVEN_PASSWORD"
            database = "defaultdb"
            ssl = true
            """
        )

        st.stop()

    mysql_config = st.secrets["mysql"]

    return {
        "host": mysql_config["host"],
        "port": int(mysql_config.get("port", 3306)),
        "user": mysql_config["user"],
        "password": mysql_config["password"],
        "database": mysql_config["database"],
        "ssl": mysql_config.get("ssl", True),
        "ssl_ca": mysql_config.get("ssl_ca", None)
    }


@contextmanager
def get_connection():

    config = get_db_config()

    connection = None

    try:

        connection_kwargs = {
            "host": config["host"],
            "port": config["port"],
            "user": config["user"],
            "password": config["password"],
            "database": config["database"],
            "cursorclass": DictCursor,
            "autocommit": False,
            "connect_timeout": 10
        }

        # ----------------------------------------------------
        # SSL AIVEN
        # ----------------------------------------------------

        if config["ssl"]:

            if config["ssl_ca"]:

                connection_kwargs["ssl"] = {
                    "ca": config["ssl_ca"]
                }

            else:

                connection_kwargs["ssl"] = {}

        connection = pymysql.connect(**connection_kwargs)

        yield connection

        connection.commit()

    except Exception:

        if connection:
            connection.rollback()

        raise

    finally:

        if connection:
            connection.close()


# ============================================================
# KHỞI TẠO DATABASE
# ============================================================

def initialize_database():

    with get_connection() as conn:

        cursor = conn.cursor()

        # ----------------------------------------------------
        # BẢNG HƯỚNG DẪN VIÊN
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tour_guides (

                id INT AUTO_INCREMENT PRIMARY KEY,

                guide_code VARCHAR(30) UNIQUE NOT NULL,

                full_name VARCHAR(150) NOT NULL,

                phone VARCHAR(30),

                email VARCHAR(150),

                languages VARCHAR(255),

                specialty VARCHAR(255),

                status ENUM(
                    'Đang làm việc',
                    'Nghỉ việc'
                ) DEFAULT 'Đang làm việc',

                created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP

            ) ENGINE=InnoDB
            """
        )

        # ----------------------------------------------------
        # BẢNG CA LÀM VIỆC
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS guide_shifts (

                id INT AUTO_INCREMENT PRIMARY KEY,

                guide_id INT NOT NULL,

                shift_date DATE NOT NULL,

                start_time TIME NOT NULL,

                end_time TIME NOT NULL,

                tour_name VARCHAR(255) NOT NULL,

                destination VARCHAR(255),

                tour_type VARCHAR(100),

                guest_count INT DEFAULT 0,

                pickup_location VARCHAR(255),

                note TEXT,

                status ENUM(
                    'Đã xếp',
                    'Đang thực hiện',
                    'Hoàn thành',
                    'Đã hủy'
                ) DEFAULT 'Đã xếp',

                created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (guide_id)
                REFERENCES tour_guides(id)
                ON DELETE CASCADE,

                INDEX idx_shift_date (shift_date),

                INDEX idx_guide_date (
                    guide_id,
                    shift_date
                )

            ) ENGINE=InnoDB
            """
        )

        # ----------------------------------------------------
        # BẢNG NGÀY NGHỈ
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS guide_days_off (

                id INT AUTO_INCREMENT PRIMARY KEY,

                guide_id INT NOT NULL,

                off_date DATE NOT NULL,

                reason VARCHAR(255),

                created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (guide_id)
                REFERENCES tour_guides(id)
                ON DELETE CASCADE,

                UNIQUE KEY unique_guide_day_off (
                    guide_id,
                    off_date
                )

            ) ENGINE=InnoDB
            """
        )


# ============================================================
# KIỂM TRA DATABASE
# ============================================================

def check_database_connection():

    try:

        initialize_database()

        with get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute(
                "SELECT 1 AS connected"
            )

            result = cursor.fetchone()

            return result is not None

    except Exception as e:

        st.error(
            "❌ Không thể kết nối MySQL Aiven."
        )

        st.code(str(e))

        st.info(
            """
            Kiểm tra lại:

            1. Host
            2. Port
            3. Username
            4. Password
            5. Database
            6. SSL
            7. Aiven service còn đang hoạt động
            """
        )

        return False


# ============================================================
# CRUD - HƯỚNG DẪN VIÊN
# ============================================================

def get_guides(include_inactive=False):

    with get_connection() as conn:

        cursor = conn.cursor()

        if include_inactive:

            cursor.execute(
                """
                SELECT *
                FROM tour_guides
                ORDER BY full_name
                """
            )

        else:

            cursor.execute(
                """
                SELECT *
                FROM tour_guides
                WHERE status = 'Đang làm việc'
                ORDER BY full_name
                """
            )

        return cursor.fetchall()


def get_guide(guide_id):

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM tour_guides
            WHERE id = %s
            """,
            (guide_id,)
        )

        return cursor.fetchone()


def add_guide(
    guide_code,
    full_name,
    phone,
    email,
    languages,
    specialty
):

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO tour_guides
            (
                guide_code,
                full_name,
                phone,
                email,
                languages,
                specialty
            )
            VALUES
            (
                %s, %s, %s, %s, %s, %s
            )
            """,
            (
                guide_code,
                full_name,
                phone,
                email,
                languages,
                specialty
            )
        )


def update_guide(
    guide_id,
    guide_code,
    full_name,
    phone,
    email,
    languages,
    specialty,
    status
):

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE tour_guides

            SET
                guide_code = %s,
                full_name = %s,
                phone = %s,
                email = %s,
                languages = %s,
                specialty = %s,
                status = %s

            WHERE id = %s
            """,
            (
                guide_code,
                full_name,
                phone,
                email,
                languages,
                specialty,
                status,
                guide_id
            )
        )


def delete_guide(guide_id):

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM tour_guides
            WHERE id = %s
            """,
            (guide_id,)
        )


# ============================================================
# CRUD - NGÀY NGHỈ
# ============================================================

def add_day_off(
    guide_id,
    off_date,
    reason
):

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO guide_days_off
            (
                guide_id,
                off_date,
                reason
            )
            VALUES
            (
                %s, %s, %s
            )
            """,
            (
                guide_id,
                off_date,
                reason
            )
        )


def get_day_offs():

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                d.id,
                d.guide_id,
                g.guide_code,
                g.full_name,
                d.off_date,
                d.reason

            FROM guide_days_off d

            JOIN tour_guides g
            ON d.guide_id = g.id

            ORDER BY
                d.off_date DESC
            """
        )

        return cursor.fetchall()


def delete_day_off(off_id):

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM guide_days_off
            WHERE id = %s
            """,
            (off_id,)
        )


# ============================================================
# KIỂM TRA NGÀY NGHỈ
# ============================================================

def is_guide_off(
    guide_id,
    shift_date
):

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id
            FROM guide_days_off

            WHERE
                guide_id = %s
                AND off_date = %s

            LIMIT 1
            """,
            (
                guide_id,
                shift_date
            )
        )

        return cursor.fetchone() is not None


# ============================================================
# KIỂM TRA TRÙNG CA
# ============================================================

def check_shift_conflict(
    guide_id,
    shift_date,
    start_time,
    end_time,
    exclude_shift_id=None
):

    with get_connection() as conn:

        cursor = conn.cursor()

        query = """
            SELECT
                s.id,
                s.start_time,
                s.end_time,
                s.tour_name,
                s.destination

            FROM guide_shifts s

            WHERE
                s.guide_id = %s
                AND s.shift_date = %s
                AND s.status != 'Đã hủy'

                AND (
                    s.start_time < %s
                    AND s.end_time > %s
                )
        """

        params = [
            guide_id,
            shift_date,
            end_time,
            start_time
        ]

        if exclude_shift_id:

            query += """
                AND s.id != %s
            """

            params.append(exclude_shift_id)

        query += """
            LIMIT 1
        """

        cursor.execute(
            query,
            tuple(params)
        )

        return cursor.fetchone()


# ============================================================
# THÊM CA
# ============================================================

def add_shift(
    guide_id,
    shift_date,
    start_time,
    end_time,
    tour_name,
    destination,
    tour_type,
    guest_count,
    pickup_location,
    note
):

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO guide_shifts
            (
                guide_id,
                shift_date,
                start_time,
                end_time,
                tour_name,
                destination,
                tour_type,
                guest_count,
                pickup_location,
                note
            )

            VALUES
            (
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s
            )
            """,
            (
                guide_id,
                shift_date,
                start_time,
                end_time,
                tour_name,
                destination,
                tour_type,
                guest_count,
                pickup_location,
                note
            )
        )


# ============================================================
# LẤY DANH SÁCH CA
# ============================================================

def get_shifts(
    selected_date=None,
    guide_id=None
):

    with get_connection() as conn:

        cursor = conn.cursor()

        query = """
            SELECT

                s.id,
                s.guide_id,

                g.guide_code,
                g.full_name,
                g.phone,

                s.shift_date,
                s.start_time,
                s.end_time,

                s.tour_name,
                s.destination,
                s.tour_type,

                s.guest_count,
                s.pickup_location,
                s.note,
                s.status

            FROM guide_shifts s

            JOIN tour_guides g
            ON s.guide_id = g.id

            WHERE 1 = 1
        """

        params = []

        if selected_date:

            query += """
                AND s.shift_date = %s
            """

            params.append(selected_date)

        if guide_id:

            query += """
                AND s.guide_id = %s
            """

            params.append(guide_id)

        query += """
            ORDER BY
                s.shift_date ASC,
                s.start_time ASC,
                g.full_name ASC
        """

        cursor.execute(
            query,
            tuple(params)
        )

        return cursor.fetchall()


# ============================================================
# XÓA CA
# ============================================================

def delete_shift(shift_id):

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM guide_shifts
            WHERE id = %s
            """,
            (shift_id,)
        )


# ============================================================
# CẬP NHẬT TRẠNG THÁI CA
# ============================================================

def update_shift_status(
    shift_id,
    status
):

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE guide_shifts

            SET status = %s

            WHERE id = %s
            """,
            (
                status,
                shift_id
            )
        )


# ============================================================
# DASHBOARD
# ============================================================

def get_dashboard_stats():

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_guides,

                SUM(
                    status = 'Đang làm việc'
                ) AS active_guides

            FROM tour_guides
            """
        )

        guide_stats = cursor.fetchone()

        cursor.execute(
            """
            SELECT

                COUNT(*) AS total_shifts,

                SUM(
                    status = 'Đã xếp'
                ) AS scheduled_shifts,

                SUM(
                    status = 'Đang thực hiện'
                ) AS running_shifts,

                SUM(
                    status = 'Hoàn thành'
                ) AS completed_shifts,

                SUM(
                    status = 'Đã hủy'
                ) AS cancelled_shifts

            FROM guide_shifts
            """
        )

        shift_stats = cursor.fetchone()

        return guide_stats, shift_stats


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="app-header">

        <h1>🧭 TOUR GUIDE SHIFT MANAGER</h1>

        <p>
            Hệ thống quản lý và phân ca hướng dẫn viên du lịch
            theo ngày
        </p>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# KIỂM TRA KẾT NỐI
# ============================================================

if not check_database_connection():
    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.image(
        "https://cdn-icons-png.flaticon.com/512/3097/3097130.png",
        width=75
    )

    st.title("Tour Guide Manager")

    st.divider()

    menu = st.radio(
        "MENU",
        [
            "📊 Dashboard",
            "👨‍💼 Quản lý HDV",
            "📅 Phân ca",
            "🗓️ Lịch phân ca",
            "🏖️ Ngày nghỉ",
            "📋 Tất cả ca"
        ]
    )

    st.divider()

    st.caption(
        "Database: MySQL Aiven"
    )

    st.caption(
        "Streamlit Application"
    )


# ============================================================
# DASHBOARD
# ============================================================

if menu == "📊 Dashboard":

    st.header("📊 Dashboard")

    guide_stats, shift_stats = get_dashboard_stats()

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "👨‍💼 Tổng HDV",
            guide_stats["total_guides"] or 0
        )

    with col2:

        st.metric(
            "🟢 HDV đang làm",
            guide_stats["active_guides"] or 0
        )

    with col3:

        st.metric(
            "📅 Tổng số ca",
            shift_stats["total_shifts"] or 0
        )

    with col4:

        st.metric(
            "⏳ Ca chờ thực hiện",
            shift_stats["scheduled_shifts"] or 0
        )

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "🔵 Đang thực hiện",
            shift_stats["running_shifts"] or 0
        )

    with col2:

        st.metric(
            "✅ Hoàn thành",
            shift_stats["completed_shifts"] or 0
        )

    with col3:

        st.metric(
            "❌ Đã hủy",
            shift_stats["cancelled_shifts"] or 0
        )

    st.divider()

    st.subheader("📅 Lịch hôm nay")

    today_shifts = get_shifts(
        selected_date=date.today()
    )

    if not today_shifts:

        st.info(
            "Hôm nay chưa có ca nào được phân."
        )

    else:

        for shift in today_shifts:

            st.markdown(
                f"""
                <div class="shift-card">

                <b>
                {shift['start_time']} -
                {shift['end_time']}
                </b>

                &nbsp;&nbsp;

                🧑‍💼 {shift['full_name']}

                <br><br>

                🗺️ {shift['tour_name']}

                &nbsp; | &nbsp;

                📍 {shift['destination']}

                &nbsp; | &nbsp;

                👥 {shift['guest_count']} khách

                </div>
                """,
                unsafe_allow_html=True
            )


# ============================================================
# QUẢN LÝ HDV
# ============================================================

elif menu == "👨‍💼 Quản lý HDV":

    st.header("👨‍💼 Quản lý hướng dẫn viên")

    tabs = st.tabs(
        [
            "➕ Thêm HDV",
            "✏️ Chỉnh sửa",
            "📋 Danh sách"
        ]
    )

    # --------------------------------------------------------
    # THÊM HDV
    # --------------------------------------------------------

    with tabs[0]:

        st.subheader(
            "➕ Thêm hướng dẫn viên"
        )

        with st.form("add_guide_form"):

            col1, col2 = st.columns(2)

            with col1:

                guide_code = st.text_input(
                    "Mã HDV *",
                    placeholder="HDV001"
                )

                full_name = st.text_input(
                    "Họ và tên *",
                    placeholder="Nguyễn Văn A"
                )

                phone = st.text_input(
                    "Số điện thoại",
                    placeholder="0901234567"
                )

            with col2:

                email = st.text_input(
                    "Email"
                )

                languages = st.text_input(
                    "Ngoại ngữ",
                    placeholder="Tiếng Anh, Tiếng Trung"
                )

                specialty = st.text_input(
                    "Chuyên môn",
                    placeholder="Nội địa, Quốc tế, Văn hóa..."
                )

            submitted = st.form_submit_button(
                "💾 Lưu hướng dẫn viên",
                type="primary"
            )

            if submitted:

                if not guide_code.strip():

                    st.error(
                        "Vui lòng nhập mã HDV."
                    )

                elif not full_name.strip():

                    st.error(
                        "Vui lòng nhập họ tên HDV."
                    )

                else:

                    try:

                        add_guide(
                            guide_code.strip(),
                            full_name.strip(),
                            phone.strip(),
                            email.strip(),
                            languages.strip(),
                            specialty.strip()
                        )

                        st.success(
                            "✅ Đã thêm hướng dẫn viên."
                        )

                        st.rerun()

                    except pymysql.err.IntegrityError:

                        st.error(
                            "❌ Mã HDV đã tồn tại."
                        )

                    except Exception as e:

                        st.error(
                            f"Lỗi: {e}"
                        )

    # --------------------------------------------------------
    # CHỈNH SỬA
    # --------------------------------------------------------

    with tabs[1]:

        guides = get_guides(
            include_inactive=True
        )

        if not guides:

            st.info(
                "Chưa có hướng dẫn viên."
            )

        else:

            guide_options = {
                f"{g['guide_code']} - {g['full_name']}":
                g["id"]
                for g in guides
            }

            selected_label = st.selectbox(
                "Chọn HDV",
                list(guide_options.keys())
            )

            selected_guide = get_guide(
                guide_options[selected_label]
            )

            with st.form("edit_guide_form"):

                col1, col2 = st.columns(2)

                with col1:

                    edit_code = st.text_input(
                        "Mã HDV",
                        value=selected_guide["guide_code"]
                    )

                    edit_name = st.text_input(
                        "Họ và tên",
                        value=selected_guide["full_name"]
                    )

                    edit_phone = st.text_input(
                        "Số điện thoại",
                        value=selected_guide["phone"] or ""
                    )

                with col2:

                    edit_email = st.text_input(
                        "Email",
                        value=selected_guide["email"] or ""
                    )

                    edit_languages = st.text_input(
                        "Ngoại ngữ",
                        value=selected_guide["languages"] or ""
                    )

                    edit_specialty = st.text_input(
                        "Chuyên môn",
                        value=selected_guide["specialty"] or ""
                    )

                    edit_status = st.selectbox(
                        "Trạng thái",
                        [
                            "Đang làm việc",
                            "Nghỉ việc"
                        ],
                        index=(
                            0
                            if selected_guide["status"]
                            == "Đang làm việc"
                            else 1
                        )
                    )

                save_edit = st.form_submit_button(
                    "💾 Cập nhật",
                    type="primary"
                )

                if save_edit:

                    try:

                        update_guide(
                            selected_guide["id"],
                            edit_code.strip(),
                            edit_name.strip(),
                            edit_phone.strip(),
                            edit_email.strip(),
                            edit_languages.strip(),
                            edit_specialty.strip(),
                            edit_status
                        )

                        st.success(
                            "Đã cập nhật HDV."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            f"Lỗi: {e}"
                        )

            st.divider()

            if st.button(
                "🗑️ Xóa HDV này",
                type="secondary"
            ):

                delete_guide(
                    selected_guide["id"]
                )

                st.success(
                    "Đã xóa HDV."
                )

                st.rerun()

    # --------------------------------------------------------
    # DANH SÁCH
    # --------------------------------------------------------

    with tabs[2]:

        guides = get_guides(
            include_inactive=True
        )

        if guides:

            for guide in guides:

                status_icon = (
                    "🟢"
                    if guide["status"]
                    == "Đang làm việc"
                    else "🔴"
                )

                with st.expander(
                    f"{status_icon} "
                    f"{guide['guide_code']} - "
                    f"{guide['full_name']}"
                ):

                    col1, col2 = st.columns(2)

                    with col1:

                        st.write(
                            f"**Điện thoại:** "
                            f"{guide['phone'] or '-'}"
                        )

                        st.write(
                            f"**Email:** "
                            f"{guide['email'] or '-'}"
                        )

                    with col2:

                        st.write(
                            f"**Ngoại ngữ:** "
                            f"{guide['languages'] or '-'}"
                        )

                        st.write(
                            f"**Chuyên môn:** "
                            f"{guide['specialty'] or '-'}"
                        )


# ============================================================
# PHÂN CA
# ============================================================

elif menu == "📅 Phân ca":

    st.header("📅 Phân ca hướng dẫn viên")

    guides = get_guides()

    if not guides:

        st.warning(
            "Chưa có HDV đang làm việc. "
            "Hãy thêm HDV trước."
        )

    else:

        guide_options = {
            f"{g['guide_code']} - {g['full_name']}":
            g["id"]
            for g in guides
        }

        with st.form("create_shift_form"):

            st.subheader(
                "1️⃣ Thông tin phân ca"
            )

            col1, col2 = st.columns(2)

            with col1:

                selected_label = st.selectbox(
                    "Hướng dẫn viên *",
                    list(guide_options.keys())
                )

                selected_guide_id = guide_options[
                    selected_label
                ]

                shift_date = st.date_input(
                    "Ngày làm việc *",
                    value=date.today()
                )

                tour_name = st.text_input(
                    "Tên tour *",
                    placeholder="Vũng Tàu 2N1Đ"
                )

                destination = st.text_input(
                    "Điểm đến",
                    placeholder="Vũng Tàu"
                )

            with col2:

                start_time = st.time_input(
                    "Giờ bắt đầu *",
                    value=time(8, 0)
                )

                end_time = st.time_input(
                    "Giờ kết thúc *",
                    value=time(17, 0)
                )

                tour_type = st.selectbox(
                    "Loại tour",
                    [
                        "Tour nội địa",
                        "Tour quốc tế",
                        "City tour",
                        "Tour đoàn",
                        "Tour ghép",
                        "Tour MICE",
                        "Tour học sinh",
                        "Tour khác"
                    ]
                )

                guest_count = st.number_input(
                    "Số lượng khách",
                    min_value=0,
                    value=20,
                    step=1
                )

            pickup_location = st.text_input(
                "Điểm đón",
                placeholder="Ví dụ: Nhà hát TP.HCM"
            )

            note = st.text_area(
                "Ghi chú",
                placeholder="Thông tin thêm cho HDV..."
            )

            submitted = st.form_submit_button(
                "📅 XẾP CA",
                type="primary",
                use_container_width=True
            )

        if submitted:

            # ------------------------------------------------
            # KIỂM TRA GIỜ
            # ------------------------------------------------

            if end_time <= start_time:

                st.error(
                    "❌ Giờ kết thúc phải lớn hơn giờ bắt đầu."
                )

            elif not tour_name.strip():

                st.error(
                    "❌ Vui lòng nhập tên tour."
                )

            else:

                # --------------------------------------------
                # KIỂM TRA NGÀY NGHỈ
                # --------------------------------------------

                if is_guide_off(
                    selected_guide_id,
                    shift_date
                ):

                    st.error(
                        "🏖️ HDV này đã đăng ký nghỉ vào ngày "
                        f"{shift_date.strftime('%d/%m/%Y')}."
                    )

                else:

                    # ----------------------------------------
                    # KIỂM TRA TRÙNG CA
                    # ----------------------------------------

                    conflict = check_shift_conflict(
                        selected_guide_id,
                        shift_date,
                        start_time,
                        end_time
                    )

                    if conflict:

                        st.error(
                            "❌ HDV đã có ca bị trùng thời gian!"
                        )

                        st.warning(
                            f"""
                            Ca hiện tại:

                            🕐 {conflict['start_time']} -
                            {conflict['end_time']}

                            🗺️ {conflict['tour_name']}

                            📍 {conflict['destination'] or '-'}
                            """
                        )

                    else:

                        try:

                            add_shift(
                                selected_guide_id,
                                shift_date,
                                start_time,
                                end_time,
                                tour_name.strip(),
                                destination.strip(),
                                tour_type,
                                guest_count,
                                pickup_location.strip(),
                                note.strip()
                            )

                            st.success(
                                "✅ Phân ca thành công!"
                            )

                            st.rerun()

                        except Exception as e:

                            st.error(
                                f"Lỗi khi lưu ca: {e}"
                            )


# ============================================================
# LỊCH PHÂN CA
# ============================================================

elif menu == "🗓️ Lịch phân ca":

    st.header("🗓️ Lịch phân ca theo ngày")

    guides = get_guides(
        include_inactive=True
    )

    col1, col2 = st.columns(2)

    with col1:

        selected_date = st.date_input(
            "📅 Chọn ngày",
            value=date.today()
        )

    with col2:

        guide_filter_options = {
            "Tất cả HDV": None
        }

        for guide in guides:

            guide_filter_options[
                f"{guide['guide_code']} - "
                f"{guide['full_name']}"
            ] = guide["id"]

        selected_guide_label = st.selectbox(
            "👨‍💼 Lọc theo HDV",
            list(guide_filter_options.keys())
        )

    selected_guide_id = guide_filter_options[
        selected_guide_label
    ]

    shifts = get_shifts(
        selected_date=selected_date,
        guide_id=selected_guide_id
    )

    st.divider()

    st.subheader(
        f"📅 Ngày {selected_date.strftime('%d/%m/%Y')}"
    )

    if not shifts:

        st.info(
            "Ngày này chưa có ca được phân."
        )

    else:

        st.success(
            f"Có {len(shifts)} ca trong ngày."
        )

        for shift in shifts:

            with st.container():

                col1, col2, col3 = st.columns(
                    [1.5, 4, 1.5]
                )

                with col1:

                    st.markdown(
                        f"""
                        ### 🕐
                        {shift['start_time']} -
                        {shift['end_time']}
                        """
                    )

                    st.caption(
                        shift["status"]
                    )

                with col2:

                    st.markdown(
                        f"### 🧑‍💼 {shift['full_name']}"
                    )

                    st.write(
                        f"🗺️ **Tour:** "
                        f"{shift['tour_name']}"
                    )

                    st.write(
                        f"📍 **Điểm đến:** "
                        f"{shift['destination'] or '-'}"
                    )

                    st.write(
                        f"👥 **Khách:** "
                        f"{shift['guest_count']}"
                    )

                    st.write(
                        f"🚐 **Điểm đón:** "
                        f"{shift['pickup_location'] or '-'}"
                    )

                with col3:

                    new_status = st.selectbox(
                        "Trạng thái",
                        [
                            "Đã xếp",
                            "Đang thực hiện",
                            "Hoàn thành",
                            "Đã hủy"
                        ],
                        index=[
                            "Đã xếp",
                            "Đang thực hiện",
                            "Hoàn thành",
                            "Đã hủy"
                        ].index(
                            shift["status"]
                        ),
                        key=f"status_{shift['id']}"
                    )

                    if st.button(
                        "💾 Cập nhật",
                        key=f"update_{shift['id']}"
                    ):

                        update_shift_status(
                            shift["id"],
                            new_status
                        )

                        st.success(
                            "Đã cập nhật."
                        )

                        st.rerun()

                    if st.button(
                        "🗑️ Xóa ca",
                        key=f"delete_{shift['id']}"
                    ):

                        delete_shift(
                            shift["id"]
                        )

                        st.success(
                            "Đã xóa ca."
                        )

                        st.rerun()

                st.divider()


# ============================================================
# NGÀY NGHỈ
# ============================================================

elif menu == "🏖️ Ngày nghỉ":

    st.header("🏖️ Quản lý ngày nghỉ HDV")

    guides = get_guides(
        include_inactive=False
    )

    if not guides:

        st.warning(
            "Chưa có HDV đang làm việc."
        )

    else:

        st.subheader(
            "➕ Đăng ký ngày nghỉ"
        )

        guide_options = {
            f"{g['guide_code']} - {g['full_name']}":
            g["id"]
            for g in guides
        }

        with st.form("day_off_form"):

            col1, col2, col3 = st.columns(3)

            with col1:

                selected_label = st.selectbox(
                    "Hướng dẫn viên",
                    list(guide_options.keys())
                )

            with col2:

                off_date = st.date_input(
                    "Ngày nghỉ",
                    value=date.today()
                )

            with col3:

                reason = st.text_input(
                    "Lý do",
                    placeholder="Nghỉ phép..."
                )

            submitted = st.form_submit_button(
                "🏖️ Lưu ngày nghỉ",
                type="primary"
            )

            if submitted:

                try:

                    add_day_off(
                        guide_options[selected_label],
                        off_date,
                        reason.strip()
                    )

                    st.success(
                        "Đã lưu ngày nghỉ."
                    )

                    st.rerun()

                except pymysql.err.IntegrityError:

                    st.error(
                        "HDV này đã có ngày nghỉ này."
                    )

                except Exception as e:

                    st.error(
                        f"Lỗi: {e}"
                    )

    st.divider()

    st.subheader(
        "📋 Danh sách ngày nghỉ"
    )

    day_offs = get_day_offs()

    if not day_offs:

        st.info(
            "Chưa có ngày nghỉ nào."
        )

    else:

        for item in day_offs:

            col1, col2, col3, col4 = st.columns(
                [2, 2, 2, 1]
            )

            with col1:

                st.write(
                    f"🧑‍💼 {item['full_name']}"
                )

            with col2:

                st.write(
                    item["off_date"].strftime(
                        "%d/%m/%Y"
                    )
                )

            with col3:

                st.write(
                    item["reason"] or "-"
                )

            with col4:

                if st.button(
                    "🗑️",
                    key=f"delete_off_{item['id']}"
                ):

                    delete_day_off(
                        item["id"]
                    )

                    st.rerun()


# ============================================================
# TẤT CẢ CA
# ============================================================

elif menu == "📋 Tất cả ca":

    st.header("📋 Tất cả ca phân công")

    guides = get_guides(
        include_inactive=True
    )

    col1, col2 = st.columns(2)

    with col1:

        filter_date = st.date_input(
            "📅 Lọc ngày",
            value=None
        )

    with col2:

        options = {
            "Tất cả HDV": None
        }

        for guide in guides:

            options[
                f"{guide['guide_code']} - "
                f"{guide['full_name']}"
            ] = guide["id"]

        selected_label = st.selectbox(
            "👨‍💼 HDV",
            list(options.keys())
        )

    filter_guide_id = options[
        selected_label
    ]

    shifts = get_shifts(
        selected_date=filter_date,
        guide_id=filter_guide_id
    )

    st.write(
        f"**Tổng số ca:** {len(shifts)}"
    )

    if shifts:

        for shift in shifts:

            with st.expander(
                f"📅 "
                f"{shift['shift_date'].strftime('%d/%m/%Y')} "
                f"| "
                f"{shift['start_time']} - "
                f"{shift['end_time']} "
                f"| "
                f"{shift['full_name']} "
                f"| "
                f"{shift['tour_name']}"
            ):

                col1, col2 = st.columns(2)

                with col1:

                    st.write(
                        f"**HDV:** "
                        f"{shift['full_name']}"
                    )

                    st.write(
                        f"**Mã HDV:** "
                        f"{shift['guide_code']}"
                    )

                    st.write(
                        f"**Tour:** "
                        f"{shift['tour_name']}"
                    )

                    st.write(
                        f"**Điểm đến:** "
                        f"{shift['destination'] or '-'}"
                    )

                    st.write(
                        f"**Loại tour:** "
                        f"{shift['tour_type'] or '-'}"
                    )

                with col2:

                    st.write(
                        f"**Ngày:** "
                        f"{shift['shift_date'].strftime('%d/%m/%Y')}"
                    )

                    st.write(
                        f"**Thời gian:** "
                        f"{shift['start_time']} - "
                        f"{shift['end_time']}"
                    )

                    st.write(
                        f"**Số khách:** "
                        f"{shift['guest_count']}"
                    )

                    st.write(
                        f"**Điểm đón:** "
                        f"{shift['pickup_location'] or '-'}"
                    )

                    st.write(
                        f"**Trạng thái:** "
                        f"{shift['status']}"
                    )

                    if shift["note"]:

                        st.write(
                            f"**Ghi chú:** "
                            f"{shift['note']}"
                        )

    else:

        st.info(
            "Không có dữ liệu phù hợp."
        )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">

        <hr>

        🧭 <b>Tour Guide Shift Manager</b>

        <br>

        Hệ thống phân ca hướng dẫn viên du lịch

        <br>

        Streamlit + MySQL + Aiven

        <br><br>

        © 2026

    </div>
    """,
    unsafe_allow_html=True
)
