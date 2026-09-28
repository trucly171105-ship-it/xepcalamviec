import streamlit as st
import pymysql
from pymysql.cursors import DictCursor
from datetime import datetime, date, time, timedelta
from contextlib import contextmanager

# ============================================================
# CẤU HÌNH TRANG
# ============================================================

st.set_page_config(
    page_title="Quản lý ca Hướng dẫn viên",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CSS GIAO DIỆN
# ============================================================

st.markdown("""
<style>
    .main-title {
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .sub-title {
        color: #666;
        margin-bottom: 25px;
    }

    .metric-card {
        padding: 15px;
        border-radius: 10px;
        background-color: #f5f7fa;
        border: 1px solid #e5e7eb;
    }

    .status-daxep {
        color: #2563eb;
        font-weight: bold;
    }

    .status-dangthuchien {
        color: #d97706;
        font-weight: bold;
    }

    .status-hoanthanh {
        color: #16a34a;
        font-weight: bold;
    }

    .status-dahuy {
        color: #dc2626;
        font-weight: bold;
    }

    div[data-testid="stMetricValue"] {
        font-size: 28px;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# KẾT NỐI AIVEN MYSQL
# ============================================================

def get_db_config():
    """
    Đọc thông tin MySQL từ:
    .streamlit/secrets.toml

    Ví dụ:

    [mysql]
    host = "..."
    port = 12345
    user = "..."
    password = "..."
    database = "defaultdb"
    ssl = true
    """

    try:
        config = {
            "host": st.secrets["mysql"]["host"],
            "port": int(st.secrets["mysql"]["port"]),
            "user": st.secrets["mysql"]["user"],
            "password": st.secrets["mysql"]["password"],
            "database": st.secrets["mysql"]["database"],
        }

        ssl_enabled = st.secrets["mysql"].get("ssl", True)

        if ssl_enabled:
            config["ssl"] = {}

        return config

    except Exception as e:
        st.error(
            "Không đọc được thông tin kết nối MySQL. "
            "Hãy kiểm tra file .streamlit/secrets.toml."
        )
        st.code(str(e))
        st.stop()


@contextmanager
def get_connection():
    config = get_db_config()

    connection = None

    try:
        connection = pymysql.connect(
            host=config["host"],
            port=config["port"],
            user=config["user"],
            password=config["password"],
            database=config["database"],
            cursorclass=DictCursor,
            autocommit=False,
            connect_timeout=15,
            read_timeout=30,
            write_timeout=30,
            ssl=config.get("ssl")
        )

        yield connection

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

def init_database():

    create_guides = """
    CREATE TABLE IF NOT EXISTS tour_guides (
        id INT AUTO_INCREMENT PRIMARY KEY,
        full_name VARCHAR(150) NOT NULL,
        phone VARCHAR(30),
        email VARCHAR(150),
        language VARCHAR(100),
        guide_type VARCHAR(100),
        experience_years INT DEFAULT 0,
        status VARCHAR(50) DEFAULT 'Đang hoạt động',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """

    create_shifts = """
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
        status VARCHAR(50) DEFAULT 'Đã xếp',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ON UPDATE CURRENT_TIMESTAMP,

        CONSTRAINT fk_shift_guide
        FOREIGN KEY (guide_id)
        REFERENCES tour_guides(id)
        ON DELETE CASCADE,

        INDEX idx_shift_date (shift_date),
        INDEX idx_guide_date (guide_id, shift_date)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """

    create_days_off = """
    CREATE TABLE IF NOT EXISTS guide_days_off (
        id INT AUTO_INCREMENT PRIMARY KEY,
        guide_id INT NOT NULL,
        off_date DATE NOT NULL,
        reason VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        CONSTRAINT fk_dayoff_guide
        FOREIGN KEY (guide_id)
        REFERENCES tour_guides(id)
        ON DELETE CASCADE,

        UNIQUE KEY unique_guide_dayoff (guide_id, off_date)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(create_guides)
            cursor.execute(create_shifts)
            cursor.execute(create_days_off)

        conn.commit()


# ============================================================
# HÀM DATABASE - HƯỚNG DẪN VIÊN
# ============================================================

def get_guides(include_inactive=False):

    with get_connection() as conn:
        with conn.cursor() as cursor:

            if include_inactive:
                cursor.execute("""
                    SELECT *
                    FROM tour_guides
                    ORDER BY full_name
                """)
            else:
                cursor.execute("""
                    SELECT *
                    FROM tour_guides
                    WHERE status = 'Đang hoạt động'
                    ORDER BY full_name
                """)

            return cursor.fetchall()


def get_guide(guide_id):

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT *
                FROM tour_guides
                WHERE id = %s
            """, (guide_id,))

            return cursor.fetchone()


def add_guide(
    full_name,
    phone,
    email,
    language,
    guide_type,
    experience_years,
    status,
    notes
):

    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
                INSERT INTO tour_guides
                (
                    full_name,
                    phone,
                    email,
                    language,
                    guide_type,
                    experience_years,
                    status,
                    notes
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                full_name,
                phone,
                email,
                language,
                guide_type,
                experience_years,
                status,
                notes
            ))

        conn.commit()


def update_guide(
    guide_id,
    full_name,
    phone,
    email,
    language,
    guide_type,
    experience_years,
    status,
    notes
):

    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
                UPDATE tour_guides
                SET
                    full_name = %s,
                    phone = %s,
                    email = %s,
                    language = %s,
                    guide_type = %s,
                    experience_years = %s,
                    status = %s,
                    notes = %s
                WHERE id = %s
            """, (
                full_name,
                phone,
                email,
                language,
                guide_type,
                experience_years,
                status,
                notes,
                guide_id
            ))

        conn.commit()


def delete_guide(guide_id):

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM tour_guides
                WHERE id = %s
            """, (guide_id,))

        conn.commit()


# ============================================================
# HÀM DATABASE - CA LÀM VIỆC
# ============================================================

def get_shifts(
    from_date=None,
    to_date=None,
    guide_id=None,
    status=None
):

    sql = """
        SELECT
            s.*,
            g.full_name,
            g.phone
        FROM guide_shifts s
        INNER JOIN tour_guides g
            ON s.guide_id = g.id
        WHERE 1=1
    """

    params = []

    if from_date:
        sql += " AND s.shift_date >= %s"
        params.append(from_date)

    if to_date:
        sql += " AND s.shift_date <= %s"
        params.append(to_date)

    if guide_id:
        sql += " AND s.guide_id = %s"
        params.append(guide_id)

    if status:
        sql += " AND s.status = %s"
        params.append(status)

    sql += """
        ORDER BY
            s.shift_date ASC,
            s.start_time ASC,
            g.full_name ASC
    """

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()


def get_shift(shift_id):

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    s.*,
                    g.full_name
                FROM guide_shifts s
                INNER JOIN tour_guides g
                    ON s.guide_id = g.id
                WHERE s.id = %s
            """, (shift_id,))

            return cursor.fetchone()


def check_shift_conflict(
    guide_id,
    shift_date,
    start_time,
    end_time,
    exclude_shift_id=None
):

    sql = """
        SELECT
            s.id,
            s.start_time,
            s.end_time,
            s.tour_name
        FROM guide_shifts s
        WHERE s.guide_id = %s
          AND s.shift_date = %s
          AND s.status <> 'Đã hủy'
          AND s.start_time < %s
          AND s.end_time > %s
    """

    params = [
        guide_id,
        shift_date,
        end_time,
        start_time
    ]

    if exclude_shift_id:
        sql += " AND s.id <> %s"
        params.append(exclude_shift_id)

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()


def is_day_off(guide_id, off_date):

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id
                FROM guide_days_off
                WHERE guide_id = %s
                  AND off_date = %s
            """, (guide_id, off_date))

            return cursor.fetchone() is not None


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
    status,
    notes
):

    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
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
                    status,
                    notes
                )
                VALUES
                (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                guide_id,
                shift_date,
                start_time,
                end_time,
                tour_name,
                destination,
                tour_type,
                guest_count,
                pickup_location,
                status,
                notes
            ))

        conn.commit()


def update_shift(
    shift_id,
    guide_id,
    shift_date,
    start_time,
    end_time,
    tour_name,
    destination,
    tour_type,
    guest_count,
    pickup_location,
    status,
    notes
):

    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
                UPDATE guide_shifts
                SET
                    guide_id = %s,
                    shift_date = %s,
                    start_time = %s,
                    end_time = %s,
                    tour_name = %s,
                    destination = %s,
                    tour_type = %s,
                    guest_count = %s,
                    pickup_location = %s,
                    status = %s,
                    notes = %s
                WHERE id = %s
            """, (
                guide_id,
                shift_date,
                start_time,
                end_time,
                tour_name,
                destination,
                tour_type,
                guest_count,
                pickup_location,
                status,
                notes,
                shift_id
            ))

        conn.commit()


def delete_shift(shift_id):

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM guide_shifts
                WHERE id = %s
            """, (shift_id,))

        conn.commit()


# ============================================================
# NGÀY NGHỈ
# ============================================================

def get_days_off():

    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT
                    d.*,
                    g.full_name
                FROM guide_days_off d
                INNER JOIN tour_guides g
                    ON d.guide_id = g.id
                ORDER BY d.off_date DESC
            """)

            return cursor.fetchall()


def add_day_off(guide_id, off_date, reason):

    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
                INSERT INTO guide_days_off
                (
                    guide_id,
                    off_date,
                    reason
                )
                VALUES (%s,%s,%s)
            """, (
                guide_id,
                off_date,
                reason
            ))

        conn.commit()


def delete_day_off(dayoff_id):

    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
                DELETE FROM guide_days_off
                WHERE id = %s
            """, (dayoff_id,))

        conn.commit()


# ============================================================
# KHỞI TẠO DATABASE
# ============================================================

try:
    init_database()

except Exception as e:
    st.error("❌ Không thể kết nối đến Aiven MySQL.")
    st.error("Hãy kiểm tra Host, Port, User, Password, Database và SSL.")
    st.code(str(e))
    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🧭 QUẢN LÝ HƯỚNG DẪN VIÊN")

menu = st.sidebar.radio(
    "Chức năng",
    [
        "📊 Tổng quan",
        "👤 Quản lý hướng dẫn viên",
        "📅 Xếp ca theo ngày",
        "🗓️ Lịch làm việc",
        "🏖️ Ngày nghỉ",
        "⚙️ Quản lý ca"
    ]
)

st.sidebar.divider()

st.sidebar.caption(
    "Ứng dụng quản lý và phân ca hướng dẫn viên du lịch"
)


# ============================================================
# TRANG TỔNG QUAN
# ============================================================

if menu == "📊 Tổng quan":

    st.markdown(
        '<div class="main-title">📊 Tổng quan hệ thống</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">Quản lý và phân ca hướng dẫn viên du lịch</div>',
        unsafe_allow_html=True
    )

    guides = get_guides(include_inactive=True)
    active_guides = [
        g for g in guides
        if g["status"] == "Đang hoạt động"
    ]

    today = date.today()

    today_shifts = get_shifts(
        from_date=today,
        to_date=today
    )

    week_end = today + timedelta(days=6)

    week_shifts = get_shifts(
        from_date=today,
        to_date=week_end
    )

    completed_today = [
        s for s in today_shifts
        if s["status"] == "Hoàn thành"
    ]

    cancelled_today = [
        s for s in today_shifts
        if s["status"] == "Đã hủy"
    ]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "👤 HDV hoạt động",
        len(active_guides)
    )

    col2.metric(
        "📅 Ca hôm nay",
        len(today_shifts)
    )

    col3.metric(
        "📆 Ca 7 ngày tới",
        len(week_shifts)
    )

    col4.metric(
        "✅ Hoàn thành hôm nay",
        len(completed_today)
    )

    st.divider()

    st.subheader("📅 Lịch làm việc hôm nay")

    if not today_shifts:

        st.info("Hôm nay chưa có ca nào được xếp.")

    else:

        display_data = []

        for s in today_shifts:

            display_data.append({
                "HDV": s["full_name"],
                "Thời gian":
                    f"{s['start_time']} - {s['end_time']}",
                "Tour": s["tour_name"],
                "Điểm đến": s["destination"],
                "Khách": s["guest_count"],
                "Trạng thái": s["status"]
            })

        st.dataframe(
            display_data,
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    st.subheader("📈 Thống kê trạng thái ca trong 7 ngày tới")

    status_counts = {
        "Đã xếp": 0,
        "Đang thực hiện": 0,
        "Hoàn thành": 0,
        "Đã hủy": 0
    }

    for s in week_shifts:

        if s["status"] in status_counts:
            status_counts[s["status"]] += 1

    chart_data = {
        "Trạng thái": list(status_counts.keys()),
        "Số ca": list(status_counts.values())
    }

    st.bar_chart(
        chart_data,
        x="Trạng thái",
        y="Số ca"
    )


# ============================================================
# QUẢN LÝ HƯỚNG DẪN VIÊN
# ============================================================

elif menu == "👤 Quản lý hướng dẫn viên":

    st.markdown(
        '<div class="main-title">👤 Quản lý hướng dẫn viên</div>',
        unsafe_allow_html=True
    )

    tab1, tab2 = st.tabs([
        "➕ Thêm hướng dẫn viên",
        "📋 Danh sách hướng dẫn viên"
    ])

    # --------------------------------------------------------
    # THÊM HDV
    # --------------------------------------------------------

    with tab1:

        with st.form("add_guide_form"):

            st.subheader("Thông tin hướng dẫn viên")

            col1, col2 = st.columns(2)

            with col1:

                full_name = st.text_input(
                    "Họ và tên *"
                )

                phone = st.text_input(
                    "Số điện thoại"
                )

                email = st.text_input(
                    "Email"
                )

                language = st.text_input(
                    "Ngoại ngữ",
                    placeholder="VD: Tiếng Anh, Tiếng Trung"
                )

            with col2:

                guide_type = st.selectbox(
                    "Loại hướng dẫn viên",
                    [
                        "HDV nội địa",
                        "HDV quốc tế",
                        "HDV theo đoàn",
                        "HDV tự do"
                    ]
                )

                experience_years = st.number_input(
                    "Số năm kinh nghiệm",
                    min_value=0,
                    max_value=50,
                    value=0
                )

                status = st.selectbox(
                    "Trạng thái",
                    [
                        "Đang hoạt động",
                        "Tạm nghỉ",
                        "Nghỉ việc"
                    ]
                )

                notes = st.text_area(
                    "Ghi chú"
                )

            submitted = st.form_submit_button(
                "➕ Thêm hướng dẫn viên",
                use_container_width=True
            )

            if submitted:

                if not full_name.strip():

                    st.error("Vui lòng nhập họ tên.")

                else:

                    try:

                        add_guide(
                            full_name.strip(),
                            phone.strip(),
                            email.strip(),
                            language.strip(),
                            guide_type,
                            experience_years,
                            status,
                            notes.strip()
                        )

                        st.success(
                            f"Đã thêm hướng dẫn viên: {full_name}"
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            f"Không thể thêm hướng dẫn viên: {e}"
                        )

    # --------------------------------------------------------
    # DANH SÁCH HDV
    # --------------------------------------------------------

    with tab2:

        guides = get_guides(include_inactive=True)

        if not guides:

            st.info("Chưa có hướng dẫn viên.")

        else:

            display_data = []

            for g in guides:

                display_data.append({
                    "ID": g["id"],
                    "Họ tên": g["full_name"],
                    "Điện thoại": g["phone"],
                    "Email": g["email"],
                    "Ngoại ngữ": g["language"],
                    "Loại HDV": g["guide_type"],
                    "Kinh nghiệm": f"{g['experience_years']} năm",
                    "Trạng thái": g["status"]
                })

            st.dataframe(
                display_data,
                use_container_width=True,
                hide_index=True
            )

            st.divider()

            st.subheader("✏️ Chỉnh sửa / Xóa hướng dẫn viên")

            guide_options = {
                f"{g['id']} - {g['full_name']}": g["id"]
                for g in guides
            }

            selected_name = st.selectbox(
                "Chọn hướng dẫn viên",
                list(guide_options.keys())
            )

            selected_id = guide_options[selected_name]

            selected_guide = get_guide(selected_id)

            if selected_guide:

                with st.form("edit_guide_form"):

                    col1, col2 = st.columns(2)

                    with col1:

                        edit_name = st.text_input(
                            "Họ và tên",
                            value=selected_guide["full_name"]
                        )

                        edit_phone = st.text_input(
                            "Số điện thoại",
                            value=selected_guide["phone"] or ""
                        )

                        edit_email = st.text_input(
                            "Email",
                            value=selected_guide["email"] or ""
                        )

                        edit_language = st.text_input(
                            "Ngoại ngữ",
                            value=selected_guide["language"] or ""
                        )

                    with col2:

                        type_options = [
                            "HDV nội địa",
                            "HDV quốc tế",
                            "HDV theo đoàn",
                            "HDV tự do"
                        ]

                        current_type = selected_guide["guide_type"]

                        type_index = (
                            type_options.index(current_type)
                            if current_type in type_options
                            else 0
                        )

                        edit_type = st.selectbox(
                            "Loại HDV",
                            type_options,
                            index=type_index
                        )

                        edit_experience = st.number_input(
                            "Số năm kinh nghiệm",
                            min_value=0,
                            max_value=50,
                            value=int(
                                selected_guide["experience_years"] or 0
                            )
                        )

                        status_options = [
                            "Đang hoạt động",
                            "Tạm nghỉ",
                            "Nghỉ việc"
                        ]

                        current_status = selected_guide["status"]

                        status_index = (
                            status_options.index(current_status)
                            if current_status in status_options
                            else 0
                        )

                        edit_status = st.selectbox(
                            "Trạng thái",
                            status_options,
                            index=status_index
                        )

                        edit_notes = st.text_area(
                            "Ghi chú",
                            value=selected_guide["notes"] or ""
                        )

                    save = st.form_submit_button(
                        "💾 Lưu thay đổi",
                        use_container_width=True
                    )

                    if save:

                        if not edit_name.strip():

                            st.error("Họ tên không được để trống.")

                        else:

                            try:

                                update_guide(
                                    selected_id,
                                    edit_name.strip(),
                                    edit_phone.strip(),
                                    edit_email.strip(),
                                    edit_language.strip(),
                                    edit_type,
                                    edit_experience,
                                    edit_status,
                                    edit_notes.strip()
                                )

                                st.success(
                                    "Đã cập nhật thông tin."
                                )

                                st.rerun()

                            except Exception as e:

                                st.error(
                                    f"Lỗi cập nhật: {e}"
                                )

                st.warning(
                    "⚠️ Xóa hướng dẫn viên sẽ xóa cả các ca và ngày nghỉ "
                    "đã liên kết với hướng dẫn viên này."
                )

                if st.button(
                    "🗑️ Xóa hướng dẫn viên",
                    type="secondary"
                ):

                    try:

                        delete_guide(selected_id)

                        st.success(
                            "Đã xóa hướng dẫn viên."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            f"Không thể xóa: {e}"
                        )


# ============================================================
# XẾP CA THEO NGÀY
# ============================================================

elif menu == "📅 Xếp ca theo ngày":

    st.markdown(
        '<div class="main-title">📅 Xếp ca hướng dẫn viên</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">'
        'Phân công hướng dẫn viên cho từng tour theo ngày và thời gian'
        '</div>',
        unsafe_allow_html=True
    )

    guides = get_guides()

    if not guides:

        st.warning(
            "Chưa có hướng dẫn viên đang hoạt động. "
            "Hãy thêm hướng dẫn viên trước."
        )

    else:

        guide_options = {
            f"{g['full_name']} | {g['guide_type']}": g["id"]
            for g in guides
        }

        with st.form("add_shift_form"):

            st.subheader("Thông tin phân ca")

            col1, col2 = st.columns(2)

            with col1:

                selected_guide_name = st.selectbox(
                    "Hướng dẫn viên *",
                    list(guide_options.keys())
                )

                selected_guide_id = guide_options[
                    selected_guide_name
                ]

                shift_date = st.date_input(
                    "Ngày làm việc *",
                    value=date.today()
                )

                start_time = st.time_input(
                    "Giờ bắt đầu *",
                    value=time(8, 0)
                )

                end_time = st.time_input(
                    "Giờ kết thúc *",
                    value=time(17, 0)
                )

            with col2:

                tour_name = st.text_input(
                    "Tên tour *",
                    placeholder="VD: Tour Vũng Tàu 1 ngày"
                )

                destination = st.text_input(
                    "Điểm đến",
                    placeholder="VD: Bạch Dinh - Tượng Chúa Kitô - Bãi Sau"
                )

                tour_type = st.selectbox(
                    "Loại tour",
                    [
                        "Tour trong ngày",
                        "Tour nhiều ngày",
                        "City tour",
                        "Tour tham quan",
                        "Tour đoàn",
                        "Tour học sinh",
                        "Tour doanh nghiệp",
                        "Khác"
                    ]
                )

                guest_count = st.number_input(
                    "Số lượng khách",
                    min_value=0,
                    max_value=10000,
                    value=20
                )

                pickup_location = st.text_input(
                    "Điểm đón khách",
                    placeholder="VD: Khách sạn ABC"
                )

                status = st.selectbox(
                    "Trạng thái ca",
                    [
                        "Đã xếp",
                        "Đang thực hiện",
                        "Hoàn thành",
                        "Đã hủy"
                    ]
                )

            notes = st.text_area(
                "Ghi chú"
            )

            submit_shift = st.form_submit_button(
                "➕ XẾP CA",
                use_container_width=True
            )

            if submit_shift:

                if not tour_name.strip():

                    st.error("Vui lòng nhập tên tour.")

                elif end_time <= start_time:

                    st.error(
                        "Giờ kết thúc phải lớn hơn giờ bắt đầu."
                    )

                elif is_day_off(
                    selected_guide_id,
                    shift_date
                ):

                    st.error(
                        "❌ Hướng dẫn viên này đã đăng ký nghỉ "
                        f"ngày {shift_date.strftime('%d/%m/%Y')}."
                    )

                else:

                    conflict = check_shift_conflict(
                        selected_guide_id,
                        shift_date,
                        start_time,
                        end_time
                    )

                    if conflict:

                        st.error(
                            "❌ Hướng dẫn viên đã có ca bị trùng giờ."
                        )

                        st.write(
                            f"Ca hiện tại: "
                            f"{conflict['start_time']} - "
                            f"{conflict['end_time']} | "
                            f"{conflict['tour_name']}"
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
                                status,
                                notes.strip()
                            )

                            st.success(
                                "✅ Đã xếp ca thành công!"
                            )

                            st.rerun()

                        except Exception as e:

                            st.error(
                                f"Không thể xếp ca: {e}"
                            )


# ============================================================
# LỊCH LÀM VIỆC
# ============================================================

elif menu == "🗓️ Lịch làm việc":

    st.markdown(
        '<div class="main-title">🗓️ Lịch làm việc</div>',
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        from_date = st.date_input(
            "Từ ngày",
            value=date.today()
        )

    with col2:

        to_date = st.date_input(
            "Đến ngày",
            value=date.today() + timedelta(days=6)
        )

    guides = get_guides(include_inactive=True)

    guide_filter_options = {
        "Tất cả hướng dẫn viên": None
    }

    for g in guides:

        guide_filter_options[
            g["full_name"]
        ] = g["id"]

    with col3:

        selected_guide_filter = st.selectbox(
            "Hướng dẫn viên",
            list(guide_filter_options.keys())
        )

    if from_date > to_date:

        st.error("Ngày bắt đầu không được lớn hơn ngày kết thúc.")

    else:

        shifts = get_shifts(
            from_date=from_date,
            to_date=to_date,
            guide_id=guide_filter_options[
                selected_guide_filter
            ]
        )

        st.write(
            f"**Tổng số ca:** {len(shifts)}"
        )

        if not shifts:

            st.info("Không có ca trong khoảng thời gian này.")

        else:

            display_data = []

            for s in shifts:

                display_data.append({
                    "Ngày":
                        s["shift_date"].strftime("%d/%m/%Y"),
                    "HDV":
                        s["full_name"],
                    "Giờ":
                        f"{s['start_time']} - {s['end_time']}",
                    "Tour":
                        s["tour_name"],
                    "Điểm đến":
                        s["destination"],
                    "Loại tour":
                        s["tour_type"],
                    "Số khách":
                        s["guest_count"],
                    "Điểm đón":
                        s["pickup_location"],
                    "Trạng thái":
                        s["status"]
                })

            st.dataframe(
                display_data,
                use_container_width=True,
                hide_index=True
            )

            st.divider()

            st.subheader("📌 Chi tiết từng ca")

            for s in shifts:

                with st.expander(
                    f"{s['shift_date'].strftime('%d/%m/%Y')} | "
                    f"{s['full_name']} | "
                    f"{s['tour_name']}"
                ):

                    c1, c2, c3 = st.columns(3)

                    c1.write(
                        f"**HDV:** {s['full_name']}"
                    )

                    c2.write(
                        f"**Thời gian:** "
                        f"{s['start_time']} - {s['end_time']}"
                    )

                    c3.write(
                        f"**Số khách:** {s['guest_count']}"
                    )

                    st.write(
                        f"**Điểm đến:** {s['destination']}"
                    )

                    st.write(
                        f"**Điểm đón:** {s['pickup_location']}"
                    )

                    st.write(
                        f"**Loại tour:** {s['tour_type']}"
                    )

                    st.write(
                        f"**Trạng thái:** {s['status']}"
                    )

                    if s["notes"]:

                        st.write(
                            f"**Ghi chú:** {s['notes']}"
                        )


# ============================================================
# NGÀY NGHỈ
# ============================================================

elif menu == "🏖️ Ngày nghỉ":

    st.markdown(
        '<div class="main-title">🏖️ Quản lý ngày nghỉ</div>',
        unsafe_allow_html=True
    )

    guides = get_guides(include_inactive=True)

    if not guides:

        st.info("Chưa có hướng dẫn viên.")

    else:

        tab1, tab2 = st.tabs([
            "➕ Đăng ký ngày nghỉ",
            "📋 Danh sách ngày nghỉ"
        ])

        with tab1:

            guide_options = {
                g["full_name"]: g["id"]
                for g in guides
            }

            with st.form("day_off_form"):

                selected_guide = st.selectbox(
                    "Hướng dẫn viên",
                    list(guide_options.keys())
                )

                off_date = st.date_input(
                    "Ngày nghỉ",
                    value=date.today()
                )

                reason = st.text_input(
                    "Lý do",
                    placeholder="VD: Nghỉ phép, việc cá nhân..."
                )

                submit_off = st.form_submit_button(
                    "🏖️ Đăng ký ngày nghỉ",
                    use_container_width=True
                )

                if submit_off:

                    try:

                        add_day_off(
                            guide_options[selected_guide],
                            off_date,
                            reason.strip()
                        )

                        st.success(
                            "Đã đăng ký ngày nghỉ."
                        )

                        st.rerun()

                    except Exception as e:

                        if "Duplicate" in str(e):

                            st.error(
                                "Hướng dẫn viên đã đăng ký nghỉ "
                                "ngày này."
                            )

                        else:

                            st.error(
                                f"Lỗi: {e}"
                            )

        with tab2:

            days_off = get_days_off()

            if not days_off:

                st.info("Chưa có ngày nghỉ nào.")

            else:

                for item in days_off:

                    c1, c2, c3, c4 = st.columns([
                        2, 2, 4, 1
                    ])

                    c1.write(
                        f"**{item['full_name']}**"
                    )

                    c2.write(
                        item["off_date"].strftime(
                            "%d/%m/%Y"
                        )
                    )

                    c3.write(
                        item["reason"] or ""
                    )

                    if c4.button(
                        "🗑️",
                        key=f"delete_off_{item['id']}"
                    ):

                        try:

                            delete_day_off(item["id"])

                            st.success(
                                "Đã xóa ngày nghỉ."
                            )

                            st.rerun()

                        except Exception as e:

                            st.error(
                                str(e)
                            )


# ============================================================
# QUẢN LÝ CA
# ============================================================

elif menu == "⚙️ Quản lý ca":

    st.markdown(
        '<div class="main-title">⚙️ Quản lý ca</div>',
        unsafe_allow_html=True
    )

    shifts = get_shifts()

    if not shifts:

        st.info("Chưa có ca nào.")

    else:

        shift_options = {
            f"#{s['id']} | "
            f"{s['shift_date'].strftime('%d/%m/%Y')} | "
            f"{s['full_name']} | "
            f"{s['tour_name']}": s["id"]
            for s in shifts
        }

        selected_shift_text = st.selectbox(
            "Chọn ca cần chỉnh sửa",
            list(shift_options.keys())
        )

        selected_shift_id = shift_options[
            selected_shift_text
        ]

        selected_shift = get_shift(
            selected_shift_id
        )

        if selected_shift:

            guides = get_guides(
                include_inactive=True
            )

            guide_options = {
                f"{g['id']} - {g['full_name']}":
                    g["id"]
                for g in guides
            }

            current_guide_text = next(
                (
                    key for key, value
                    in guide_options.items()
                    if value == selected_shift["guide_id"]
                ),
                list(guide_options.keys())[0]
            )

            with st.form("edit_shift_form"):

                col1, col2 = st.columns(2)

                with col1:

                    edit_guide_text = st.selectbox(
                        "Hướng dẫn viên",
                        list(guide_options.keys()),
                        index=list(
                            guide_options.keys()
                        ).index(current_guide_text)
                    )

                    edit_guide_id = guide_options[
                        edit_guide_text
                    ]

                    edit_date = st.date_input(
                        "Ngày",
                        value=selected_shift[
                            "shift_date"
                        ]
                    )

                    edit_start = st.time_input(
                        "Giờ bắt đầu",
                        value=(
                            selected_shift["start_time"]
                            if isinstance(
                                selected_shift["start_time"],
                                time
                            )
                            else (
                                datetime.strptime(
                                    str(
                                        selected_shift[
                                            "start_time"
                                        ]
                                    ),
                                    "%H:%M:%S"
                                ).time()
                            )
                        )
                    )

                    edit_end = st.time_input(
                        "Giờ kết thúc",
                        value=(
                            selected_shift["end_time"]
                            if isinstance(
                                selected_shift["end_time"],
                                time
                            )
                            else (
                                datetime.strptime(
                                    str(
                                        selected_shift[
                                            "end_time"
                                        ]
                                    ),
                                    "%H:%M:%S"
                                ).time()
                            )
                        )
                    )

                with col2:

                    edit_tour = st.text_input(
                        "Tên tour",
                        value=selected_shift[
                            "tour_name"
                        ]
                    )

                    edit_destination = st.text_input(
                        "Điểm đến",
                        value=selected_shift[
                            "destination"
                        ] or ""
                    )

                    tour_type_options = [
                        "Tour trong ngày",
                        "Tour nhiều ngày",
                        "City tour",
                        "Tour tham quan",
                        "Tour đoàn",
                        "Tour học sinh",
                        "Tour doanh nghiệp",
                        "Khác"
                    ]

                    current_tour_type = selected_shift[
                        "tour_type"
                    ]

                    tour_type_index = (
                        tour_type_options.index(
                            current_tour_type
                        )
                        if current_tour_type
                        in tour_type_options
                        else 0
                    )

                    edit_tour_type = st.selectbox(
                        "Loại tour",
                        tour_type_options,
                        index=tour_type_index
                    )

                    edit_guest_count = st.number_input(
                        "Số khách",
                        min_value=0,
                        max_value=10000,
                        value=int(
                            selected_shift[
                                "guest_count"
                            ] or 0
                        )
                    )

                    edit_pickup = st.text_input(
                        "Điểm đón",
                        value=selected_shift[
                            "pickup_location"
                        ] or ""
                    )

                    status_options = [
                        "Đã xếp",
                        "Đang thực hiện",
                        "Hoàn thành",
                        "Đã hủy"
                    ]

                    current_status = selected_shift[
                        "status"
                    ]

                    status_index = (
                        status_options.index(
                            current_status
                        )
                        if current_status in status_options
                        else 0
                    )

                    edit_status = st.selectbox(
                        "Trạng thái",
                        status_options,
                        index=status_index
                    )

                edit_notes = st.text_area(
                    "Ghi chú",
                    value=selected_shift[
                        "notes"
                    ] or ""
                )

                save_shift = st.form_submit_button(
                    "💾 Lưu thay đổi",
                    use_container_width=True
                )

                if save_shift:

                    if not edit_tour.strip():

                        st.error(
                            "Tên tour không được để trống."
                        )

                    elif edit_end <= edit_start:

                        st.error(
                            "Giờ kết thúc phải lớn hơn "
                            "giờ bắt đầu."
                        )

                    elif is_day_off(
                        edit_guide_id,
                        edit_date
                    ):

                        st.error(
                            "Hướng dẫn viên đã đăng ký "
                            "nghỉ ngày này."
                        )

                    else:

                        conflict = check_shift_conflict(
                            edit_guide_id,
                            edit_date,
                            edit_start,
                            edit_end,
                            exclude_shift_id=selected_shift_id
                        )

                        if conflict:

                            st.error(
                                "❌ Ca mới bị trùng với ca khác: "
                                f"{conflict['tour_name']} "
                                f"({conflict['start_time']} - "
                                f"{conflict['end_time']})"
                            )

                        else:

                            try:

                                update_shift(
                                    selected_shift_id,
                                    edit_guide_id,
                                    edit_date,
                                    edit_start,
                                    edit_end,
                                    edit_tour.strip(),
                                    edit_destination.strip(),
                                    edit_tour_type,
                                    edit_guest_count,
                                    edit_pickup.strip(),
                                    edit_status,
                                    edit_notes.strip()
                                )

                                st.success(
                                    "Đã cập nhật ca."
                                )

                                st.rerun()

                            except Exception as e:

                                st.error(
                                    f"Lỗi cập nhật ca: {e}"
                                )

            st.divider()

            if st.button(
                "🗑️ Xóa ca này",
                type="secondary"
            ):

                try:

                    delete_shift(
                        selected_shift_id
                    )

                    st.success(
                        "Đã xóa ca."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Không thể xóa ca: {e}"
                    )
