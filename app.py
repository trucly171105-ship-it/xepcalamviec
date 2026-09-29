import streamlit as st
import pandas as pd
from datetime import datetime, date, time, timedelta
import io
import uuid
import pymysql
from pymysql.cursors import DictCursor

# ============================================================
# CẤU HÌNH TRANG
# ============================================================

st.set_page_config(
    page_title="TourGuide Shift Manager",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# THÔNG TIN MYSQL AIVEN
# ============================================================

DB_HOST = "mysql-d660cbf-trucly171105-b953.k.aivencloud.com"
DB_PORT = 27221
DB_USER = "avnadmin"
DB_PASSWORD = "AVNS_cyQyD8Ez8n3Ggy-ax8l"

# Aiven MySQL thường có database mặc định là defaultdb
DB_NAME = "defaultdb"

# ============================================================
# CSS
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

    .warning-box {
        padding: 12px;
        border-radius: 8px;
        background: #fff3cd;
        border: 1px solid #ffe69c;
    }

    .success-box {
        padding: 12px;
        border-radius: 8px;
        background: #d1e7dd;
        border: 1px solid #a3cfbb;
    }

    .danger-box {
        padding: 12px;
        border-radius: 8px;
        background: #f8d7da;
        border: 1px solid #f1aeb5;
    }

    div[data-testid="stMetric"] {
        border: 1px solid #ddd;
        padding: 10px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# KẾT NỐI DATABASE
# ============================================================

@st.cache_resource
def get_connection():
    """
    Tạo kết nối MySQL Aiven.
    SSL được bật để kết nối an toàn.
    """

    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=True,

        # SSL/TLS
        ssl={
            "ssl": {}
        }
    )


def test_database_connection():
    try:
        conn = get_connection()

        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 AS test")
            cursor.fetchone()

        return True, "Kết nối MySQL Aiven thành công."

    except Exception as e:
        return False, str(e)


# ============================================================
# TẠO TABLE
# ============================================================

def create_tables():

    conn = get_connection()

    with conn.cursor() as cursor:

        # ----------------------------------------------------
        # BẢNG HDV
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS guides (
                id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                phone VARCHAR(50),
                languages TEXT,
                areas TEXT,
                specialty VARCHAR(255),
                rating DECIMAL(3,2) DEFAULT 0,
                max_shifts INT DEFAULT 5,
                status VARCHAR(50) DEFAULT 'Sẵn sàng',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            CHARACTER SET utf8mb4
            COLLATE utf8mb4_unicode_ci
        """)

        # ----------------------------------------------------
        # BẢNG TOUR
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tours (
                id VARCHAR(50) PRIMARY KEY,
                tour_name VARCHAR(255) NOT NULL,
                tour_date DATE NOT NULL,
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                location VARCHAR(255),
                tour_type VARCHAR(255),
                language VARCHAR(100),
                guests INT DEFAULT 1,
                priority VARCHAR(50) DEFAULT 'Bình thường',
                guide VARCHAR(255) DEFAULT '',
                status VARCHAR(50) DEFAULT 'Chưa phân',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            CHARACTER SET utf8mb4
            COLLATE utf8mb4_unicode_ci
        """)

        # ----------------------------------------------------
        # BẢNG THÔNG BÁO
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                message TEXT NOT NULL,
                level VARCHAR(50) DEFAULT 'info',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            CHARACTER SET utf8mb4
            COLLATE utf8mb4_unicode_ci
        """)

    conn.commit()


# ============================================================
# KHỞI TẠO DATABASE
# ============================================================

def initialize_database():

    try:

        create_tables()

        conn = get_connection()

        with conn.cursor() as cursor:

            # ------------------------------------------------
            # KIỂM TRA HDV
            # ------------------------------------------------

            cursor.execute(
                "SELECT COUNT(*) AS total FROM guides"
            )

            guide_count = cursor.fetchone()["total"]

            if guide_count == 0:

                sample_guides = [
                    (
                        "HDV001",
                        "Nguyễn Văn An",
                        "0901000001",
                        "Tiếng Việt, English",
                        "Vũng Tàu, TP.HCM",
                        "Biển đảo",
                        4.8,
                        5,
                        "Sẵn sàng"
                    ),
                    (
                        "HDV002",
                        "Trần Minh Anh",
                        "0901000002",
                        "Tiếng Việt, Trung",
                        "Vũng Tàu, Phú Quốc",
                        "Nghỉ dưỡng",
                        4.7,
                        4,
                        "Sẵn sàng"
                    ),
                    (
                        "HDV003",
                        "Lê Hoàng Nam",
                        "0901000003",
                        "Tiếng Việt, English, Korean",
                        "Đà Lạt, TP.HCM",
                        "MICE",
                        4.9,
                        6,
                        "Sẵn sàng"
                    ),
                    (
                        "HDV004",
                        "Phạm Thu Hà",
                        "0901000004",
                        "Tiếng Việt, English",
                        "Phú Quốc, Vũng Tàu",
                        "Gia đình",
                        4.6,
                        5,
                        "Sẵn sàng"
                    )
                ]

                cursor.executemany("""
                    INSERT INTO guides
                    (
                        id,
                        name,
                        phone,
                        languages,
                        areas,
                        specialty,
                        rating,
                        max_shifts,
                        status
                    )
                    VALUES
                    (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, sample_guides)

            # ------------------------------------------------
            # KIỂM TRA TOUR
            # ------------------------------------------------

            cursor.execute(
                "SELECT COUNT(*) AS total FROM tours"
            )

            tour_count = cursor.fetchone()["total"]

            if tour_count == 0:

                today = date.today()

                sample_tours = [
                    (
                        "TOUR001",
                        "Vũng Tàu 1 ngày",
                        today,
                        time(7, 30),
                        time(17, 0),
                        "Vũng Tàu",
                        "Biển đảo",
                        "Tiếng Việt",
                        30,
                        "Bình thường",
                        "",
                        "Chưa phân"
                    ),
                    (
                        "TOUR002",
                        "Phú Quốc 3N2Đ",
                        today + timedelta(days=1),
                        time(8, 0),
                        time(18, 0),
                        "Phú Quốc",
                        "Nghỉ dưỡng",
                        "Tiếng Việt",
                        20,
                        "Cao",
                        "",
                        "Chưa phân"
                    )
                ]

                cursor.executemany("""
                    INSERT INTO tours
                    (
                        id,
                        tour_name,
                        tour_date,
                        start_time,
                        end_time,
                        location,
                        tour_type,
                        language,
                        guests,
                        priority,
                        guide,
                        status
                    )
                    VALUES
                    (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, sample_tours)

        conn.commit()

    except Exception as e:
        st.error(
            f"❌ Không thể khởi tạo database: {e}"
        )
        st.stop()


# ============================================================
# LOAD DATA
# ============================================================

def load_guides():

    conn = get_connection()

    query = """
        SELECT
            id,
            name,
            phone,
            languages,
            areas,
            specialty,
            rating,
            max_shifts,
            status
        FROM guides
        ORDER BY name
    """

    return pd.read_sql(query, conn)


def load_tours():

    conn = get_connection()

    query = """
        SELECT
            id,
            tour_name,
            tour_date AS date,
            start_time AS start,
            end_time AS end,
            location,
            tour_type,
            language,
            guests,
            priority,
            guide,
            status
        FROM tours
        ORDER BY tour_date, start_time
    """

    df = pd.read_sql(query, conn)

    if not df.empty:

        df["date"] = pd.to_datetime(
            df["date"]
        ).dt.date

        df["start"] = pd.to_datetime(
            df["start"].astype(str)
        ).dt.time

        df["end"] = pd.to_datetime(
            df["end"].astype(str)
        ).dt.time

    return df


# ============================================================
# LƯU HDV
# ============================================================

def add_guide(
    guide_id,
    name,
    phone,
    languages,
    areas,
    specialty,
    rating,
    max_shifts
):

    conn = get_connection()

    with conn.cursor() as cursor:

        cursor.execute("""
            INSERT INTO guides
            (
                id,
                name,
                phone,
                languages,
                areas,
                specialty,
                rating,
                max_shifts,
                status
            )
            VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            guide_id,
            name,
            phone,
            languages,
            areas,
            specialty,
            rating,
            max_shifts,
            "Sẵn sàng"
        ))

    conn.commit()


# ============================================================
# XÓA HDV
# ============================================================

def delete_guide(name):

    conn = get_connection()

    with conn.cursor() as cursor:

        cursor.execute(
            "DELETE FROM guides WHERE name = %s",
            (name,)
        )

    conn.commit()


# ============================================================
# THÊM TOUR
# ============================================================

def add_tour(
    tour_id,
    tour_name,
    tour_date,
    start_time,
    end_time,
    location,
    tour_type,
    language,
    guests,
    priority
):

    conn = get_connection()

    with conn.cursor() as cursor:

        cursor.execute("""
            INSERT INTO tours
            (
                id,
                tour_name,
                tour_date,
                start_time,
                end_time,
                location,
                tour_type,
                language,
                guests,
                priority,
                guide,
                status
            )
            VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            tour_id,
            tour_name,
            tour_date,
            start_time,
            end_time,
            location,
            tour_type,
            language,
            guests,
            priority,
            "",
            "Chưa phân"
        ))

    conn.commit()


# ============================================================
# CẬP NHẬT PHÂN CA
# ============================================================

def update_tour_assignment(
    tour_id,
    guide,
    status
):

    conn = get_connection()

    with conn.cursor() as cursor:

        cursor.execute("""
            UPDATE tours
            SET
                guide = %s,
                status = %s
            WHERE id = %s
        """, (
            guide,
            status,
            tour_id
        ))

    conn.commit()


# ============================================================
# ĐẾM SỐ CA HDV
# ============================================================

def get_shift_count(guide_name):

    conn = get_connection()

    with conn.cursor() as cursor:

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM tours
            WHERE guide = %s
            AND status = 'Đã phân'
        """, (guide_name,))

        result = cursor.fetchone()

    return result["total"]


# ============================================================
# LẤY TOUR CỦA HDV
# ============================================================

def get_guide_tours(guide_name):

    tours = load_tours()

    return tours[
        tours["guide"] == guide_name
    ]


# ============================================================
# CHUYỂN GIỜ THÀNH PHÚT
# ============================================================

def time_to_minutes(t):

    return t.hour * 60 + t.minute


# ============================================================
# KIỂM TRA XUNG ĐỘT
# ============================================================

def has_conflict(
    guide_name,
    tour_date,
    start_time,
    end_time,
    ignore_id=None
):

    tours = load_tours()

    if tours.empty:
        return False

    for _, row in tours.iterrows():

        if ignore_id and row["id"] == ignore_id:
            continue

        if row["guide"] != guide_name:
            continue

        if row["date"] != tour_date:
            continue

        if row["status"] != "Đã phân":
            continue

        existing_start = time_to_minutes(
            row["start"]
        )

        existing_end = time_to_minutes(
            row["end"]
        )

        new_start = time_to_minutes(
            start_time
        )

        new_end = time_to_minutes(
            end_time
        )

        # Trùng thời gian
        if (
            new_start < existing_end
            and
            new_end > existing_start
        ):
            return True

        # Không đủ 2 giờ nghỉ
        if abs(
            new_start - existing_end
        ) < 120:
            return True

        if abs(
            existing_start - new_end
        ) < 120:
            return True

    return False


# ============================================================
# TÍNH ĐIỂM HDV
# ============================================================

def calculate_guide_score(
    guide,
    tour
):

    score = 0

    # --------------------------------------------------------
    # NGÔN NGỮ
    # --------------------------------------------------------

    if guide["languages"]:

        if (
            str(tour["language"]).lower()
            in
            str(guide["languages"]).lower()
        ):
            score += 35

    # --------------------------------------------------------
    # KHU VỰC
    # --------------------------------------------------------

    if guide["areas"]:

        if (
            str(tour["location"]).lower()
            in
            str(guide["areas"]).lower()
        ):
            score += 25

    # --------------------------------------------------------
    # CHUYÊN MÔN
    # --------------------------------------------------------

    if guide["specialty"]:

        if (
            str(tour["tour_type"]).lower()
            in
            str(guide["specialty"]).lower()
        ):
            score += 20

    # --------------------------------------------------------
    # RATING
    # --------------------------------------------------------

    score += float(
        guide["rating"]
    ) * 3

    # --------------------------------------------------------
    # TẢI CÔNG VIỆC
    # --------------------------------------------------------

    current = get_shift_count(
        guide["name"]
    )

    max_shift = int(
        guide["max_shifts"]
    )

    if current < max_shift:
        score += 15
    else:
        score -= 30

    # --------------------------------------------------------
    # XUNG ĐỘT
    # --------------------------------------------------------

    if has_conflict(
        guide["name"],
        tour["date"],
        tour["start"],
        tour["end"]
    ):
        score -= 100

    return round(
        score,
        2
    )


# ============================================================
# ĐỀ XUẤT HDV
# ============================================================

def recommend_guides(tour):

    guides = load_guides()

    recommendations = []

    for _, guide in guides.iterrows():

        if guide["status"] != "Sẵn sàng":
            continue

        score = calculate_guide_score(
            guide,
            tour
        )

        conflict = has_conflict(
            guide["name"],
            tour["date"],
            tour["start"],
            tour["end"]
        )

        recommendations.append({
            "HDV": guide["name"],
            "Điểm phù hợp": score,
            "Kinh nghiệm": guide["specialty"],
            "Ngôn ngữ": guide["languages"],
            "Khu vực": guide["areas"],
            "Số ca hiện tại": get_shift_count(
                guide["name"]
            ),
            "Trùng lịch": (
                "Có"
                if conflict
                else "Không"
            )
        })

    result = pd.DataFrame(
        recommendations
    )

    if not result.empty:

        result = result.sort_values(
            by="Điểm phù hợp",
            ascending=False
        )

    return result


# ============================================================
# THÔNG BÁO
# ============================================================

def save_notification(
    message,
    level="info"
):

    conn = get_connection()

    with conn.cursor() as cursor:

        cursor.execute("""
            INSERT INTO notifications
            (
                message,
                level
            )
            VALUES
            (%s,%s)
        """, (
            message,
            level
        ))

    conn.commit()


def load_notifications():

    conn = get_connection()

    query = """
        SELECT
            id,
            message,
            level,
            created_at
        FROM notifications
        ORDER BY id DESC
        LIMIT 5
    """

    return pd.read_sql(
        query,
        conn
    )


# ============================================================
# XUẤT EXCEL
# ============================================================

def dataframe_to_excel(df):

    output = io.BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Lich_phan_ca"
        )

    return output.getvalue()


# ============================================================
# KHỞI TẠO DATABASE
# ============================================================

try:

    initialize_database()

except Exception as e:

    st.error(
        "❌ Không thể kết nối MySQL Aiven."
    )

    st.code(
        str(e)
    )

    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title(
    "🧭 TourGuide Manager"
)

menu = st.sidebar.radio(
    "Chức năng",
    [
        "📊 Tổng quan",
        "👨‍✈️ Quản lý hướng dẫn viên",
        "🚌 Quản lý tour",
        "📅 Phân ca theo ngày",
        "🤖 Trợ lý xếp ca",
        "⚠️ Kiểm tra xung đột",
        "📈 Báo cáo & xuất dữ liệu"
    ]
)

st.sidebar.markdown("---")

# Kiểm tra kết nối

connected, message = test_database_connection()

if connected:

    st.sidebar.success(
        "🟢 MySQL Aiven: Đã kết nối"
    )

else:

    st.sidebar.error(
        "🔴 MySQL: Mất kết nối"
    )

st.sidebar.markdown("---")

st.sidebar.info(
    "Dữ liệu được lưu trực tiếp trên "
    "MySQL Aiven Database."
)

# ============================================================
# 1. DASHBOARD
# ============================================================

if menu == "📊 Tổng quan":

    st.markdown(
        '<div class="main-title">'
        '🧭 TourGuide Shift Manager'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">'
        'Hệ thống quản lý và phân ca '
        'hướng dẫn viên du lịch'
        '</div>',
        unsafe_allow_html=True
    )

    guides = load_guides()
    tours = load_tours()

    total_guides = len(guides)
    total_tours = len(tours)

    assigned = len(
        tours[
            tours["status"] == "Đã phân"
        ]
    )

    unassigned = len(
        tours[
            tours["status"] == "Chưa phân"
        ]
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "👨‍✈️ Tổng HDV",
        total_guides
    )

    c2.metric(
        "🚌 Tổng tour",
        total_tours
    )

    c3.metric(
        "✅ Đã phân",
        assigned
    )

    c4.metric(
        "⏳ Chưa phân",
        unassigned
    )

    st.markdown("---")

    st.subheader(
        "📅 Lịch tour"
    )

    if not tours.empty:

        display = tours.copy()

        display["date"] = display[
            "date"
        ].apply(
            lambda x:
            x.strftime("%d/%m/%Y")
            if hasattr(
                x,
                "strftime"
            )
            else x
        )

        st.dataframe(
            display[
                [
                    "tour_name",
                    "date",
                    "start",
                    "end",
                    "location",
                    "tour_type",
                    "language",
                    "guests",
                    "guide",
                    "status"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

    st.markdown("---")

    st.subheader(
        "📊 Tải công việc HDV"
    )

    workload = []

    for _, guide in guides.iterrows():

        count = get_shift_count(
            guide["name"]
        )

        workload.append({
            "HDV": guide["name"],
            "Số ca": count,
            "Tối đa": guide["max_shifts"],
            "Tỷ lệ sử dụng (%)": round(
                count /
                max(
                    int(
                        guide["max_shifts"]
                    ),
                    1
                )
                * 100,
                1
            )
        })

    workload_df = pd.DataFrame(
        workload
    )

    if not workload_df.empty:

        st.dataframe(
            workload_df,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# 2. QUẢN LÝ HDV
# ============================================================

elif menu == "👨‍✈️ Quản lý hướng dẫn viên":

    st.title(
        "👨‍✈️ Quản lý hướng dẫn viên"
    )

    tab1, tab2 = st.tabs(
        [
            "Danh sách HDV",
            "Thêm HDV"
        ]
    )

    with tab1:

        guides = load_guides()

        st.dataframe(
            guides,
            use_container_width=True,
            hide_index=True
        )

        st.markdown(
            "### 🗑️ Xóa HDV"
        )

        if not guides.empty:

            selected = st.selectbox(
                "Chọn HDV",
                guides["name"]
            )

            if st.button(
                "Xóa HDV"
            ):

                delete_guide(
                    selected
                )

                save_notification(
                    f"Đã xóa HDV {selected}.",
                    "info"
                )

                st.success(
                    "Đã xóa HDV."
                )

                st.rerun()

    with tab2:

        with st.form(
            "add_guide"
        ):

            name = st.text_input(
                "Họ và tên"
            )

            phone = st.text_input(
                "Số điện thoại"
            )

            languages = st.text_input(
                "Ngôn ngữ",
                placeholder=(
                    "Ví dụ: Tiếng Việt, English"
                )
            )

            areas = st.text_input(
                "Khu vực hoạt động",
                placeholder=(
                    "Ví dụ: Vũng Tàu, Phú Quốc"
                )
            )

            specialty = st.selectbox(
                "Chuyên môn",
                [
                    "Biển đảo",
                    "Nghỉ dưỡng",
                    "MICE",
                    "Gia đình",
                    "Văn hóa",
                    "Khác"
                ]
            )

            rating = st.slider(
                "Đánh giá",
                1.0,
                5.0,
                4.5,
                0.1
            )

            max_shifts = st.number_input(
                "Số ca tối đa/tuần",
                min_value=1,
                max_value=14,
                value=5
            )

            submitted = st.form_submit_button(
                "➕ Thêm HDV"
            )

            if submitted:

                if not name.strip():

                    st.error(
                        "Vui lòng nhập họ tên."
                    )

                else:

                    guide_id = (
                        "HDV"
                        +
                        uuid.uuid4()
                        .hex[:8]
                        .upper()
                    )

                    try:

                        add_guide(
                            guide_id,
                            name,
                            phone,
                            languages,
                            areas,
                            specialty,
                            rating,
                            max_shifts
                        )

                        save_notification(
                            f"Đã thêm HDV {name}.",
                            "success"
                        )

                        st.success(
                            f"Đã thêm HDV {name}."
                        )

                    except Exception as e:

                        st.error(
                            f"Không thể thêm HDV: {e}"
                        )


# ============================================================
# 3. QUẢN LÝ TOUR
# ============================================================

elif menu == "🚌 Quản lý tour":

    st.title(
        "🚌 Quản lý tour"
    )

    tab1, tab2 = st.tabs(
        [
            "Danh sách tour",
            "Thêm tour"
        ]
    )

    with tab1:

        tours = load_tours()

        st.dataframe(
            tours,
            use_container_width=True,
            hide_index=True
        )

    with tab2:

        with st.form(
            "add_tour"
        ):

            tour_name = st.text_input(
                "Tên tour"
            )

            tour_date = st.date_input(
                "Ngày tour",
                value=date.today()
            )

            col1, col2 = st.columns(2)

            with col1:

                start_time = st.time_input(
                    "Giờ bắt đầu",
                    value=time(7, 30)
                )

            with col2:

                end_time = st.time_input(
                    "Giờ kết thúc",
                    value=time(17, 0)
                )

            location = st.text_input(
                "Điểm đến",
                placeholder="Ví dụ: Vũng Tàu"
            )

            tour_type = st.selectbox(
                "Loại tour",
                [
                    "Biển đảo",
                    "Nghỉ dưỡng",
                    "MICE",
                    "Gia đình",
                    "Văn hóa",
                    "Khám phá",
                    "Khác"
                ]
            )

            language = st.selectbox(
                "Ngôn ngữ khách",
                [
                    "Tiếng Việt",
                    "English",
                    "Trung",
                    "Korean",
                    "Japanese"
                ]
            )

            guests = st.number_input(
                "Số khách",
                min_value=1,
                max_value=1000,
                value=20
            )

            priority = st.selectbox(
                "Mức độ ưu tiên",
                [
                    "Bình thường",
                    "Cao",
                    "Khẩn cấp"
                ]
            )

            submitted = st.form_submit_button(
                "➕ Thêm tour"
            )

            if submitted:

                if not tour_name.strip():

                    st.error(
                        "Vui lòng nhập tên tour."
                    )

                elif end_time <= start_time:

                    st.error(
                        "Giờ kết thúc phải sau "
                        "giờ bắt đầu."
                    )

                else:

                    tour_id = (
                        "TOUR"
                        +
                        uuid.uuid4()
                        .hex[:8]
                        .upper()
                    )

                    try:

                        add_tour(
                            tour_id,
                            tour_name,
                            tour_date,
                            start_time,
                            end_time,
                            location,
                            tour_type,
                            language,
                            guests,
                            priority
                        )

                        save_notification(
                            f"Đã tạo tour {tour_name}.",
                            "success"
                        )

                        st.success(
                            f"Đã tạo tour: {tour_name}"
                        )

                    except Exception as e:

                        st.error(
                            f"Không thể tạo tour: {e}"
                        )


# ============================================================
# 4. PHÂN CA THEO NGÀY
# ============================================================

elif menu == "📅 Phân ca theo ngày":

    st.title(
        "📅 Phân ca hướng dẫn viên theo ngày"
    )

    tours = load_tours()
    guides = load_guides()

    selected_date = st.date_input(
        "Chọn ngày",
        value=date.today()
    )

    daily_tours = tours[
        tours["date"] == selected_date
    ].copy()

    if daily_tours.empty:

        st.info(
            "Không có tour nào trong ngày "
            "được chọn."
        )

    else:

        for _, row in daily_tours.iterrows():

            with st.container(
                border=True
            ):

                c1, c2, c3 = st.columns(
                    [3, 2, 2]
                )

                with c1:

                    st.markdown(
                        f"### 🚌 "
                        f"{row['tour_name']}"
                    )

                    st.write(
                        f"📍 {row['location']} | "
                        f"👥 {row['guests']} khách"
                    )

                with c2:

                    st.write(
                        f"🕐 {row['start']} - "
                        f"{row['end']}"
                    )

                    st.write(
                        f"🌐 {row['language']}"
                    )

                    st.write(
                        f"⭐ {row['priority']}"
                    )

                with c3:

                    guide_options = [
                        "-- Chưa phân --"
                    ] + list(
                        guides["name"]
                    )

                    current_guide = (
                        row["guide"]
                    )

                    current_index = (
                        guide_options.index(
                            current_guide
                        )
                        if current_guide
                        in guide_options
                        else 0
                    )

                    selected_guide = st.selectbox(
                        "HDV",
                        guide_options,
                        index=current_index,
                        key=(
                            f"guide_"
                            f"{row['id']}"
                        )
                    )

                    if st.button(
                        "💾 Lưu phân ca",
                        key=(
                            f"save_"
                            f"{row['id']}"
                        )
                    ):

                        if (
                            selected_guide
                            == "-- Chưa phân --"
                        ):

                            update_tour_assignment(
                                row["id"],
                                "",
                                "Chưa phân"
                            )

                            st.warning(
                                "Tour đang ở "
                                "trạng thái chưa phân."
                            )

                            st.rerun()

                        else:

                            conflict = has_conflict(
                                selected_guide,
                                row["date"],
                                row["start"],
                                row["end"],
                                ignore_id=row["id"]
                            )

                            if conflict:

                                st.error(
                                    f"⚠️ "
                                    f"{selected_guide} "
                                    "đang bị trùng lịch "
                                    "hoặc không đủ "
                                    "thời gian nghỉ."
                                )

                            else:

                                update_tour_assignment(
                                    row["id"],
                                    selected_guide,
                                    "Đã phân"
                                )

                                save_notification(
                                    f"Đã phân "
                                    f"{row['tour_name']} "
                                    f"cho "
                                    f"{selected_guide}.",
                                    "success"
                                )

                                st.success(
                                    "Đã lưu phân ca."
                                )

                                st.rerun()

    st.markdown("---")

    st.subheader(
        "📌 Tóm tắt ca trong ngày"
    )

    if not daily_tours.empty:

        summary = (
            daily_tours[
                daily_tours["guide"] != ""
            ]
            .groupby("guide")
            .size()
            .reset_index(
                name="Số ca"
            )
        )

        if not summary.empty:

            st.dataframe(
                summary,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "Chưa có HDV nào được phân."
            )


# ============================================================
# 5. TRỢ LÝ XẾP CA
# ============================================================

elif menu == "🤖 Trợ lý xếp ca":

    st.title(
        "🤖 Trợ lý xếp ca thông minh"
    )

    st.write(
        "Hệ thống chấm điểm HDV dựa trên "
        "ngôn ngữ, khu vực, chuyên môn, "
        "rating, tải công việc và xung đột lịch."
    )

    tours = load_tours()

    unassigned = tours[
        tours["status"] == "Chưa phân"
    ]

    if unassigned.empty:

        st.success(
            "🎉 Tất cả tour hiện tại "
            "đã được phân ca."
        )

    else:

        selected_id = st.selectbox(
            "Chọn tour cần tìm HDV",
            unassigned["id"],
            format_func=lambda x:
                unassigned.loc[
                    unassigned["id"] == x,
                    "tour_name"
                ].iloc[0]
        )

        tour = tours[
            tours["id"] == selected_id
        ].iloc[0]

        st.markdown(
            "### 📋 Thông tin tour"
        )

        info1, info2, info3, info4 = st.columns(4)

        info1.metric(
            "Ngày",
            tour["date"].strftime(
                "%d/%m/%Y"
            )
        )

        info2.metric(
            "Thời gian",
            f"{tour['start']} - "
            f"{tour['end']}"
        )

        info3.metric(
            "Khách",
            tour["guests"]
        )

        info4.metric(
            "Ngôn ngữ",
            tour["language"]
        )

        if st.button(
            "🤖 Tìm HDV phù hợp",
            type="primary"
        ):

            recommendations = (
                recommend_guides(
                    tour
                )
            )

            if recommendations.empty:

                st.error(
                    "Không tìm thấy HDV phù hợp."
                )

            else:

                st.subheader(
                    "🎯 HDV được đề xuất"
                )

                st.dataframe(
                    recommendations,
                    use_container_width=True,
                    hide_index=True
                )

                valid = recommendations[
                    recommendations[
                        "Trùng lịch"
                    ] == "Không"
                ]

                if not valid.empty:

                    best = valid.iloc[0]

                    st.markdown(
                        f"""
                        <div class="success-box">
                        <b>💡 Gợi ý từ hệ thống:</b><br>
                        HDV: {best["HDV"]}<br>
                        Điểm phù hợp:
                        {best["Điểm phù hợp"]}<br>
                        Chuyên môn:
                        {best["Kinh nghiệm"]}<br>
                        Khu vực:
                        {best["Khu vực"]}<br>
                        Số ca hiện tại:
                        {best["Số ca hiện tại"]}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    if st.button(
                        f"✅ Phân tour cho "
                        f"{best['HDV']}"
                    ):

                        conflict = has_conflict(
                            best["HDV"],
                            tour["date"],
                            tour["start"],
                            tour["end"],
                            ignore_id=tour["id"]
                        )

                        if conflict:

                            st.error(
                                "Không thể phân vì "
                                "HDV bị xung đột lịch."
                            )

                        else:

                            update_tour_assignment(
                                tour["id"],
                                best["HDV"],
                                "Đã phân"
                            )

                            save_notification(
                                f"Trợ lý đã phân "
                                f"{tour['tour_name']} "
                                f"cho {best['HDV']}.",
                                "success"
                            )

                            st.success(
                                "Đã phân ca thành công!"
                            )

                            st.rerun()


# ============================================================
# 6. KIỂM TRA XUNG ĐỘT
# ============================================================

elif menu == "⚠️ Kiểm tra xung đột":

    st.title(
        "⚠️ Kiểm tra xung đột lịch"
    )

    tours = load_tours()

    assigned = tours[
        tours["status"] == "Đã phân"
    ]

    conflicts = []

    for guide_name in assigned[
        "guide"
    ].unique():

        guide_tours = assigned[
            assigned["guide"] == guide_name
        ].sort_values(
            ["date", "start"]
        )

        previous = None

        for _, row in guide_tours.iterrows():

            if previous is not None:

                if (
                    row["date"]
                    ==
                    previous["date"]
                ):

                    prev_end = time_to_minutes(
                        previous["end"]
                    )

                    current_start = (
                        time_to_minutes(
                            row["start"]
                        )
                    )

                    if current_start < prev_end:

                        conflicts.append({
                            "HDV": guide_name,
                            "Ngày": row["date"],
                            "Tour 1":
                                previous[
                                    "tour_name"
                                ],
                            "Tour 2":
                                row[
                                    "tour_name"
                                ],
                            "Lỗi":
                                "Trùng thời gian"
                        })

                    elif (
                        current_start
                        -
                        prev_end
                        < 120
                    ):

                        conflicts.append({
                            "HDV": guide_name,
                            "Ngày": row["date"],
                            "Tour 1":
                                previous[
                                    "tour_name"
                                ],
                            "Tour 2":
                                row[
                                    "tour_name"
                                ],
                            "Lỗi":
                                "Thời gian nghỉ dưới 2 giờ"
                        })

            previous = row

    if not conflicts:

        st.markdown(
            """
            <div class="success-box">
            ✅ Không phát hiện xung đột lịch.
            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        st.markdown(
            f"""
            <div class="danger-box">
            ⚠️ Phát hiện {len(conflicts)}
            vấn đề cần xử lý.
            </div>
            """,
            unsafe_allow_html=True
        )

        st.dataframe(
            pd.DataFrame(conflicts),
            use_container_width=True,
            hide_index=True
        )

    st.markdown("---")

    st.subheader(
        "📌 Kiểm tra tải công việc"
    )

    guides = load_guides()

    workload = []

    for _, guide in guides.iterrows():

        count = get_shift_count(
            guide["name"]
        )

        workload.append({
            "HDV": guide["name"],
            "Số ca": count,
            "Giới hạn": guide["max_shifts"],
            "Trạng thái":
                "⚠️ Quá tải"
                if count >
                int(
                    guide["max_shifts"]
                )
                else
                "✅ Bình thường"
        })

    st.dataframe(
        pd.DataFrame(workload),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 7. BÁO CÁO
# ============================================================

elif menu == "📈 Báo cáo & xuất dữ liệu":

    st.title(
        "📈 Báo cáo & xuất dữ liệu"
    )

    tours = load_tours()
    guides = load_guides()

    st.subheader(
        "📊 Thống kê"
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Tổng số tour",
        len(tours)
    )

    col2.metric(
        "Tour đã phân",
        len(
            tours[
                tours["status"]
                == "Đã phân"
            ]
        )
    )

    col3.metric(
        "Tour chưa phân",
        len(
            tours[
                tours["status"]
                == "Chưa phân"
            ]
        )
    )

    st.markdown("---")

    st.subheader(
        "📋 Báo cáo phân ca"
    )

    report = tours[
        [
            "id",
            "tour_name",
            "date",
            "start",
            "end",
            "location",
            "tour_type",
            "language",
            "guests",
            "priority",
            "guide",
            "status"
        ]
    ].copy()

    st.dataframe(
        report,
        use_container_width=True,
        hide_index=True
    )

    # --------------------------------------------------------
    # EXCEL
    # --------------------------------------------------------

    excel_data = dataframe_to_excel(
        report
    )

    st.download_button(
        label="📥 Tải báo cáo Excel",
        data=excel_data,
        file_name=(
            "lich_phan_ca_"
            +
            datetime.now().strftime(
                "%Y%m%d_%H%M"
            )
            +
            ".xlsx"
        ),
        mime=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        )
    )

    # --------------------------------------------------------
    # CSV
    # --------------------------------------------------------

    csv_data = report.to_csv(
        index=False
    ).encode(
        "utf-8-sig"
    )

    st.download_button(
        label="📥 Tải dữ liệu CSV",
        data=csv_data,
        file_name="lich_phan_ca.csv",
        mime="text/csv"
    )

    st.markdown("---")

    st.subheader(
        "📊 Thống kê theo HDV"
    )

    guide_report = []

    for _, guide in guides.iterrows():

        count = get_shift_count(
            guide["name"]
        )

        guide_report.append({
            "Mã HDV": guide["id"],
            "Họ tên": guide["name"],
            "Số ca": count,
            "Giới hạn": guide["max_shifts"],
            "Rating": guide["rating"],
            "Tình trạng":
                guide["status"]
        })

    st.dataframe(
        pd.DataFrame(
            guide_report
        ),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# THÔNG BÁO
# ============================================================

st.sidebar.markdown("---")

st.sidebar.subheader(
    "🔔 Thông báo"
)

try:

    notifications = (
        load_notifications()
    )

    if not notifications.empty:

        for _, notification in (
            notifications.iterrows()
        ):

            message = (
                f"{notification['message']}"
            )

            if (
                notification["level"]
                == "success"
            ):

                st.sidebar.success(
                    message
                )

            else:

                st.sidebar.info(
                    message
                )

    else:

        st.sidebar.caption(
            "Chưa có thông báo mới."
        )

except Exception:

    st.sidebar.caption(
        "Không tải được thông báo."
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "🧭 TourGuide Shift Manager | "
    "MySQL Aiven Database | "
    "Quản lý phân ca hướng dẫn viên du lịch"
)
