import streamlit as st
import pandas as pd
from datetime import datetime, date, time, timedelta
import io
import uuid

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

    .metric-card {
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #ddd;
        background: white;
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
# KHỞI TẠO DỮ LIỆU
# ============================================================

def init_data():
    if "guides" not in st.session_state:
        st.session_state.guides = pd.DataFrame([
            {
                "id": "HDV001",
                "name": "Nguyễn Văn An",
                "phone": "0901000001",
                "languages": "Tiếng Việt, English",
                "areas": "Vũng Tàu, TP.HCM",
                "specialty": "Biển đảo",
                "rating": 4.8,
                "max_shifts": 5,
                "status": "Sẵn sàng"
            },
            {
                "id": "HDV002",
                "name": "Trần Minh Anh",
                "phone": "0901000002",
                "languages": "Tiếng Việt, Trung",
                "areas": "Vũng Tàu, Phú Quốc",
                "specialty": "Nghỉ dưỡng",
                "rating": 4.7,
                "max_shifts": 4,
                "status": "Sẵn sàng"
            },
            {
                "id": "HDV003",
                "name": "Lê Hoàng Nam",
                "phone": "0901000003",
                "languages": "Tiếng Việt, English, Korean",
                "areas": "Đà Lạt, TP.HCM",
                "specialty": "MICE",
                "rating": 4.9,
                "max_shifts": 6,
                "status": "Sẵn sàng"
            },
            {
                "id": "HDV004",
                "name": "Phạm Thu Hà",
                "phone": "0901000004",
                "languages": "Tiếng Việt, English",
                "areas": "Phú Quốc, Vũng Tàu",
                "specialty": "Gia đình",
                "rating": 4.6,
                "max_shifts": 5,
                "status": "Sẵn sàng"
            },
        ])

    if "tours" not in st.session_state:
        st.session_state.tours = pd.DataFrame([
            {
                "id": "TOUR001",
                "tour_name": "Vũng Tàu 1 ngày",
                "date": date.today(),
                "start": time(7, 30),
                "end": time(17, 0),
                "location": "Vũng Tàu",
                "tour_type": "Biển đảo",
                "language": "Tiếng Việt",
                "guests": 30,
                "priority": "Bình thường",
                "guide": "",
                "status": "Chưa phân"
            },
            {
                "id": "TOUR002",
                "tour_name": "Phú Quốc 3N2Đ",
                "date": date.today() + timedelta(days=1),
                "start": time(8, 0),
                "end": time(18, 0),
                "location": "Phú Quốc",
                "tour_type": "Nghỉ dưỡng",
                "language": "Tiếng Việt",
                "guests": 20,
                "priority": "Cao",
                "guide": "",
                "status": "Chưa phân"
            }
        ])

    if "notifications" not in st.session_state:
        st.session_state.notifications = []

    if "availability" not in st.session_state:
        st.session_state.availability = {}


init_data()

# ============================================================
# HÀM TIỆN ÍCH
# ============================================================

def save_notification(message, level="info"):
    st.session_state.notifications.insert(
        0,
        {
            "time": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "message": message,
            "level": level
        }
    )


def get_shift_count(guide_name):
    tours = st.session_state.tours
    if tours.empty:
        return 0

    return len(
        tours[
            (tours["guide"] == guide_name) &
            (tours["status"] == "Đã phân")
        ]
    )


def get_guide_tours(guide_name):
    return st.session_state.tours[
        st.session_state.tours["guide"] == guide_name
    ]


def time_to_minutes(t):
    return t.hour * 60 + t.minute


def has_conflict(guide_name, tour_date, start_time, end_time, ignore_id=None):
    tours = st.session_state.tours

    for _, row in tours.iterrows():

        if ignore_id and row["id"] == ignore_id:
            continue

        if row["guide"] != guide_name:
            continue

        if row["date"] != tour_date:
            continue

        if row["status"] != "Đã phân":
            continue

        existing_start = time_to_minutes(row["start"])
        existing_end = time_to_minutes(row["end"])

        new_start = time_to_minutes(start_time)
        new_end = time_to_minutes(end_time)

        # Có giao nhau
        if new_start < existing_end and new_end > existing_start:
            return True

        # Khoảng nghỉ tối thiểu 2 tiếng
        if abs(new_start - existing_end) < 120:
            return True

        if abs(existing_start - new_end) < 120:
            return True

    return False


def calculate_guide_score(guide, tour):
    score = 0

    # Ngôn ngữ
    if guide["languages"]:
        if tour["language"].lower() in guide["languages"].lower():
            score += 35

    # Khu vực
    if guide["areas"]:
        if tour["location"].lower() in guide["areas"].lower():
            score += 25

    # Chuyên môn
    if guide["specialty"]:
        if tour["tour_type"].lower() in guide["specialty"].lower():
            score += 20

    # Rating
    score += float(guide["rating"]) * 3

    # Tải công việc
    current = get_shift_count(guide["name"])
    max_shift = int(guide["max_shifts"])

    if current < max_shift:
        score += 15
    else:
        score -= 30

    # Không trùng lịch
    if has_conflict(
        guide["name"],
        tour["date"],
        tour["start"],
        tour["end"]
    ):
        score -= 100

    return round(score, 2)


def recommend_guides(tour):
    recommendations = []

    for _, guide in st.session_state.guides.iterrows():

        if guide["status"] != "Sẵn sàng":
            continue

        score = calculate_guide_score(guide, tour)

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
            "Số ca hiện tại": get_shift_count(guide["name"]),
            "Trùng lịch": "Có" if conflict else "Không"
        })

    result = pd.DataFrame(recommendations)

    if not result.empty:
        result = result.sort_values(
            by="Điểm phù hợp",
            ascending=False
        )

    return result


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
# SIDEBAR
# ============================================================

st.sidebar.title("🧭 TourGuide Manager")

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

st.sidebar.info(
    "Ứng dụng quản lý và phân ca hướng dẫn viên du lịch."
)

# ============================================================
# 1. DASHBOARD
# ============================================================

if menu == "📊 Tổng quan":

    st.markdown(
        '<div class="main-title">🧭 TourGuide Shift Manager</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">'
        'Hệ thống quản lý và phân ca hướng dẫn viên du lịch'
        '</div>',
        unsafe_allow_html=True
    )

    guides = st.session_state.guides
    tours = st.session_state.tours

    total_guides = len(guides)
    total_tours = len(tours)
    assigned = len(tours[tours["status"] == "Đã phân"])
    unassigned = len(tours[tours["status"] == "Chưa phân"])

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("👨‍✈️ Tổng HDV", total_guides)
    c2.metric("🚌 Tổng tour", total_tours)
    c3.metric("✅ Đã phân", assigned)
    c4.metric("⏳ Chưa phân", unassigned)

    st.markdown("---")

    st.subheader("📅 Lịch tour gần nhất")

    if not tours.empty:

        display = tours.copy()

        display["date"] = display["date"].apply(
            lambda x: x.strftime("%d/%m/%Y")
            if hasattr(x, "strftime") else x
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

    st.subheader("📊 Tải công việc của HDV")

    workload = []

    for _, guide in guides.iterrows():
        workload.append({
            "HDV": guide["name"],
            "Số ca": get_shift_count(guide["name"]),
            "Tối đa": guide["max_shifts"],
            "Tỷ lệ sử dụng (%)": round(
                get_shift_count(guide["name"]) /
                max(guide["max_shifts"], 1) * 100,
                1
            )
        })

    workload_df = pd.DataFrame(workload)

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

    st.title("👨‍✈️ Quản lý hướng dẫn viên")

    tab1, tab2 = st.tabs([
        "Danh sách HDV",
        "Thêm HDV"
    ])

    with tab1:

        st.dataframe(
            st.session_state.guides,
            use_container_width=True,
            hide_index=True
        )

        st.markdown("### 🗑️ Xóa HDV")

        if not st.session_state.guides.empty:

            selected = st.selectbox(
                "Chọn HDV",
                st.session_state.guides["name"]
            )

            if st.button(
                "Xóa HDV",
                type="secondary"
            ):
                st.session_state.guides = (
                    st.session_state.guides[
                        st.session_state.guides["name"] != selected
                    ]
                )

                st.success("Đã xóa HDV.")
                st.rerun()

    with tab2:

        with st.form("add_guide"):

            name = st.text_input("Họ và tên")
            phone = st.text_input("Số điện thoại")
            languages = st.text_input(
                "Ngôn ngữ",
                placeholder="Ví dụ: Tiếng Việt, English"
            )
            areas = st.text_input(
                "Khu vực hoạt động",
                placeholder="Ví dụ: Vũng Tàu, Phú Quốc"
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
                    st.error("Vui lòng nhập họ tên.")
                else:

                    new_guide = pd.DataFrame([{
                        "id": "HDV" + uuid.uuid4().hex[:6].upper(),
                        "name": name,
                        "phone": phone,
                        "languages": languages,
                        "areas": areas,
                        "specialty": specialty,
                        "rating": rating,
                        "max_shifts": max_shifts,
                        "status": "Sẵn sàng"
                    }])

                    st.session_state.guides = pd.concat(
                        [
                            st.session_state.guides,
                            new_guide
                        ],
                        ignore_index=True
                    )

                    st.success(
                        f"Đã thêm HDV {name}."
                    )


# ============================================================
# 3. QUẢN LÝ TOUR
# ============================================================

elif menu == "🚌 Quản lý tour":

    st.title("🚌 Quản lý tour")

    tab1, tab2 = st.tabs([
        "Danh sách tour",
        "Thêm tour"
    ])

    with tab1:

        st.dataframe(
            st.session_state.tours,
            use_container_width=True,
            hide_index=True
        )

    with tab2:

        with st.form("add_tour"):

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
                    st.error("Vui lòng nhập tên tour.")

                elif end_time <= start_time:
                    st.error(
                        "Giờ kết thúc phải sau giờ bắt đầu."
                    )

                else:

                    new_tour = pd.DataFrame([{
                        "id": "TOUR" + uuid.uuid4().hex[:6].upper(),
                        "tour_name": tour_name,
                        "date": tour_date,
                        "start": start_time,
                        "end": end_time,
                        "location": location,
                        "tour_type": tour_type,
                        "language": language,
                        "guests": guests,
                        "priority": priority,
                        "guide": "",
                        "status": "Chưa phân"
                    }])

                    st.session_state.tours = pd.concat(
                        [
                            st.session_state.tours,
                            new_tour
                        ],
                        ignore_index=True
                    )

                    st.success(
                        f"Đã tạo tour: {tour_name}"
                    )


# ============================================================
# 4. PHÂN CA THEO NGÀY
# ============================================================

elif menu == "📅 Phân ca theo ngày":

    st.title("📅 Phân ca hướng dẫn viên theo ngày")

    tours = st.session_state.tours

    selected_date = st.date_input(
        "Chọn ngày",
        value=date.today()
    )

    daily_tours = tours[
        tours["date"] == selected_date
    ].copy()

    if daily_tours.empty:

        st.info(
            "Không có tour nào trong ngày được chọn."
        )

    else:

        for index, row in daily_tours.iterrows():

            with st.container(border=True):

                c1, c2, c3 = st.columns([3, 2, 2])

                with c1:
                    st.markdown(
                        f"### 🚌 {row['tour_name']}"
                    )

                    st.write(
                        f"📍 {row['location']} | "
                        f"👥 {row['guests']} khách"
                    )

                with c2:

                    st.write(
                        f"🕐 {row['start']} - {row['end']}"
                    )

                    st.write(
                        f"🌐 {row['language']}"
                    )

                with c3:

                    current_guide = row["guide"]

                    guide_options = ["-- Chưa phân --"] + \
                        list(st.session_state.guides["name"])

                    current_index = (
                        guide_options.index(current_guide)
                        if current_guide in guide_options
                        else 0
                    )

                    selected_guide = st.selectbox(
                        "HDV",
                        guide_options,
                        index=current_index,
                        key=f"guide_{row['id']}"
                    )

                    if st.button(
                        "💾 Lưu phân ca",
                        key=f"save_{row['id']}"
                    ):

                        if selected_guide == "-- Chưa phân --":

                            st.session_state.tours.at[
                                index,
                                "guide"
                            ] = ""

                            st.session_state.tours.at[
                                index,
                                "status"
                            ] = "Chưa phân"

                            st.warning(
                                "Tour đang ở trạng thái chưa phân."
                            )

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
                                    f"⚠️ {selected_guide} "
                                    "đang bị trùng lịch hoặc "
                                    "không đủ thời gian nghỉ."
                                )

                            else:

                                st.session_state.tours.at[
                                    index,
                                    "guide"
                                ] = selected_guide

                                st.session_state.tours.at[
                                    index,
                                    "status"
                                ] = "Đã phân"

                                save_notification(
                                    f"Đã phân {row['tour_name']} "
                                    f"cho {selected_guide}.",
                                    "success"
                                )

                                st.success(
                                    "Đã lưu phân ca."
                                )

    st.markdown("---")

    st.subheader("📌 Tóm tắt ca trong ngày")

    if not daily_tours.empty:

        summary = daily_tours[
            daily_tours["guide"] != ""
        ].groupby("guide").size().reset_index(
            name="Số ca"
        )

        if not summary.empty:
            st.dataframe(
                summary,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Chưa có HDV nào được phân.")


# ============================================================
# 5. TRỢ LÝ XẾP CA THÔNG MINH
# ============================================================

elif menu == "🤖 Trợ lý xếp ca":

    st.title("🤖 Trợ lý xếp ca thông minh")

    st.write(
        "Hệ thống chấm điểm HDV dựa trên ngôn ngữ, "
        "khu vực, chuyên môn, rating, tải công việc "
        "và xung đột lịch."
    )

    tours = st.session_state.tours

    unassigned = tours[
        tours["status"] == "Chưa phân"
    ]

    if unassigned.empty:

        st.success(
            "🎉 Tất cả tour hiện tại đã được phân ca."
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

        st.markdown("### 📋 Thông tin tour")

        info1, info2, info3, info4 = st.columns(4)

        info1.metric(
            "Ngày",
            tour["date"].strftime("%d/%m/%Y")
        )

        info2.metric(
            "Thời gian",
            f"{tour['start']} - {tour['end']}"
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

            recommendations = recommend_guides(
                tour
            )

            if recommendations.empty:

                st.error(
                    "Không tìm thấy HDV phù hợp."
                )

            else:

                st.subheader(
                    "🎯 Danh sách HDV được đề xuất"
                )

                st.dataframe(
                    recommendations,
                    use_container_width=True,
                    hide_index=True
                )

                valid = recommendations[
                    recommendations["Trùng lịch"] == "Không"
                ]

                if not valid.empty:

                    best = valid.iloc[0]

                    st.markdown(
                        f"""
                        <div class="success-box">
                        <b>💡 Gợi ý từ hệ thống:</b><br>
                        {best["HDV"]}<br>
                        Điểm phù hợp: {best["Điểm phù hợp"]}<br>
                        Chuyên môn: {best["Kinh nghiệm"]}<br>
                        Khu vực: {best["Khu vực"]}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    if st.button(
                        f"✅ Phân tour cho {best['HDV']}"
                    ):

                        idx = st.session_state.tours[
                            st.session_state.tours["id"]
                            == selected_id
                        ].index[0]

                        st.session_state.tours.at[
                            idx,
                            "guide"
                        ] = best["HDV"]

                        st.session_state.tours.at[
                            idx,
                            "status"
                        ] = "Đã phân"

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

    st.title("⚠️ Kiểm tra xung đột lịch")

    tours = st.session_state.tours

    assigned = tours[
        tours["status"] == "Đã phân"
    ]

    conflicts = []

    for guide_name in assigned["guide"].unique():

        guide_tours = assigned[
            assigned["guide"] == guide_name
        ].sort_values(
            ["date", "start"]
        )

        previous = None

        for _, row in guide_tours.iterrows():

            if previous is not None:

                if row["date"] == previous["date"]:

                    prev_end = time_to_minutes(
                        previous["end"]
                    )

                    current_start = time_to_minutes(
                        row["start"]
                    )

                    if current_start < prev_end:

                        conflicts.append({
                            "HDV": guide_name,
                            "Ngày": row["date"],
                            "Tour 1": previous["tour_name"],
                            "Tour 2": row["tour_name"],
                            "Lỗi": "Trùng thời gian"
                        })

                    elif current_start - prev_end < 120:

                        conflicts.append({
                            "HDV": guide_name,
                            "Ngày": row["date"],
                            "Tour 1": previous["tour_name"],
                            "Tour 2": row["tour_name"],
                            "Lỗi": "Thời gian nghỉ dưới 2 giờ"
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
            ⚠️ Phát hiện {len(conflicts)} vấn đề cần xử lý.
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

    st.subheader("📌 Kiểm tra tải công việc")

    workload = []

    for _, guide in st.session_state.guides.iterrows():

        count = get_shift_count(
            guide["name"]
        )

        workload.append({
            "HDV": guide["name"],
            "Số ca": count,
            "Giới hạn": guide["max_shifts"],
            "Trạng thái":
                "⚠️ Quá tải"
                if count > guide["max_shifts"]
                else "✅ Bình thường"
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

    st.title("📈 Báo cáo & xuất dữ liệu")

    tours = st.session_state.tours
    guides = st.session_state.guides

    st.subheader("📊 Thống kê")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Tổng số tour",
        len(tours)
    )

    col2.metric(
        "Tour đã phân",
        len(
            tours[
                tours["status"] == "Đã phân"
            ]
        )
    )

    col3.metric(
        "Tour chưa phân",
        len(
            tours[
                tours["status"] == "Chưa phân"
            ]
        )
    )

    st.markdown("---")

    st.subheader("📋 Báo cáo phân ca")

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

    excel_data = dataframe_to_excel(
        report
    )

    st.download_button(
        label="📥 Tải báo cáo Excel",
        data=excel_data,
        file_name=(
            f"lich_phan_ca_"
            f"{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        ),
        mime=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        )
    )

    csv_data = report.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        label="📥 Tải dữ liệu CSV",
        data=csv_data,
        file_name="lich_phan_ca.csv",
        mime="text/csv"
    )

    st.markdown("---")

    st.subheader("📊 Thống kê theo HDV")

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
            "Tình trạng": guide["status"]
        })

    st.dataframe(
        pd.DataFrame(guide_report),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# THÔNG BÁO
# ============================================================

st.sidebar.markdown("---")

st.sidebar.subheader("🔔 Thông báo")

if st.session_state.notifications:

    for notification in st.session_state.notifications[:5]:

        if notification["level"] == "success":
            st.sidebar.success(
                notification["message"]
            )
        else:
            st.sidebar.info(
                notification["message"]
            )

else:

    st.sidebar.caption(
        "Chưa có thông báo mới."
    )

# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "🧭 TourGuide Shift Manager | "
    "Ứng dụng quản lý phân ca hướng dẫn viên du lịch"
)
