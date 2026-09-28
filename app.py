import streamlit as st
from datetime import datetime, date, time, timedelta

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

div[data-testid="stMetricValue"] {
    font-size: 28px;
}

[data-testid="stSidebar"] {
    border-right: 1px solid #e5e7eb;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# KHỞI TẠO DỮ LIỆU
# ============================================================

if "guides" not in st.session_state:
    st.session_state.guides = []

if "shifts" not in st.session_state:
    st.session_state.shifts = []

if "days_off" not in st.session_state:
    st.session_state.days_off = []

if "next_guide_id" not in st.session_state:
    st.session_state.next_guide_id = 1

if "next_shift_id" not in st.session_state:
    st.session_state.next_shift_id = 1

if "next_dayoff_id" not in st.session_state:
    st.session_state.next_dayoff_id = 1


# ============================================================
# HÀM TIỆN ÍCH
# ============================================================

def get_guide(guide_id):
    for guide in st.session_state.guides:
        if guide["id"] == guide_id:
            return guide
    return None


def get_shift(shift_id):
    for shift in st.session_state.shifts:
        if shift["id"] == shift_id:
            return shift
    return None


def get_active_guides():
    return [
        guide
        for guide in st.session_state.guides
        if guide["status"] == "Đang hoạt động"
    ]


def is_day_off(guide_id, off_date):
    for item in st.session_state.days_off:
        if (
            item["guide_id"] == guide_id
            and item["off_date"] == off_date
        ):
            return True
    return False


def check_shift_conflict(
    guide_id,
    shift_date,
    start_time,
    end_time,
    exclude_shift_id=None
):
    """
    Kiểm tra hai ca có bị trùng thời gian hay không.

    Hai ca bị xem là trùng khi:
    ca mới bắt đầu trước khi ca cũ kết thúc
    VÀ
    ca mới kết thúc sau khi ca cũ bắt đầu.
    """

    for shift in st.session_state.shifts:

        if exclude_shift_id is not None:
            if shift["id"] == exclude_shift_id:
                continue

        if shift["guide_id"] != guide_id:
            continue

        if shift["shift_date"] != shift_date:
            continue

        if shift["status"] == "Đã hủy":
            continue

        if (
            start_time < shift["end_time"]
            and end_time > shift["start_time"]
        ):
            return shift

    return None


def format_date(value):
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    return str(value)


def format_time(value):
    if isinstance(value, time):
        return value.strftime("%H:%M")
    return str(value)


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

st.sidebar.info(
    "Ứng dụng quản lý và phân ca "
    "hướng dẫn viên du lịch."
)

st.sidebar.caption(
    f"👤 HDV: {len(st.session_state.guides)}"
)

st.sidebar.caption(
    f"📅 Tổng ca: {len(st.session_state.shifts)}"
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
        '<div class="sub-title">'
        'Quản lý và phân ca hướng dẫn viên du lịch'
        '</div>',
        unsafe_allow_html=True
    )

    today = date.today()

    active_guides = get_active_guides()

    today_shifts = [
        shift
        for shift in st.session_state.shifts
        if shift["shift_date"] == today
    ]

    week_end = today + timedelta(days=6)

    week_shifts = [
        shift
        for shift in st.session_state.shifts
        if today <= shift["shift_date"] <= week_end
    ]

    completed_today = [
        shift
        for shift in today_shifts
        if shift["status"] == "Hoàn thành"
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

    # --------------------------------------------------------
    # LỊCH HÔM NAY
    # --------------------------------------------------------

    st.subheader("📅 Lịch làm việc hôm nay")

    if not today_shifts:

        st.info("Hôm nay chưa có ca nào được xếp.")

    else:

        display_data = []

        for shift in sorted(
            today_shifts,
            key=lambda x: x["start_time"]
        ):

            guide = get_guide(
                shift["guide_id"]
            )

            display_data.append({
                "HDV":
                    guide["full_name"]
                    if guide else "Không xác định",

                "Thời gian":
                    f"{format_time(shift['start_time'])}"
                    f" - "
                    f"{format_time(shift['end_time'])}",

                "Tour":
                    shift["tour_name"],

                "Điểm đến":
                    shift["destination"],

                "Khách":
                    shift["guest_count"],

                "Trạng thái":
                    shift["status"]
            })

        st.dataframe(
            display_data,
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    # --------------------------------------------------------
    # THỐNG KÊ
    # --------------------------------------------------------

    st.subheader(
        "📈 Thống kê trạng thái ca trong 7 ngày tới"
    )

    status_counts = {
        "Đã xếp": 0,
        "Đang thực hiện": 0,
        "Hoàn thành": 0,
        "Đã hủy": 0
    }

    for shift in week_shifts:

        if shift["status"] in status_counts:
            status_counts[
                shift["status"]
            ] += 1

    chart_data = {
        "Trạng thái": list(
            status_counts.keys()
        ),
        "Số ca": list(
            status_counts.values()
        )
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
        '<div class="main-title">'
        '👤 Quản lý hướng dẫn viên'
        '</div>',
        unsafe_allow_html=True
    )

    tab1, tab2 = st.tabs([
        "➕ Thêm hướng dẫn viên",
        "📋 Danh sách hướng dẫn viên"
    ])

    # ========================================================
    # THÊM HDV
    # ========================================================

    with tab1:

        with st.form("add_guide_form"):

            st.subheader(
                "Thông tin hướng dẫn viên"
            )

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
                    placeholder=(
                        "VD: Tiếng Anh, Tiếng Trung"
                    )
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

                    st.error(
                        "Vui lòng nhập họ tên."
                    )

                else:

                    new_guide = {
                        "id":
                            st.session_state.next_guide_id,

                        "full_name":
                            full_name.strip(),

                        "phone":
                            phone.strip(),

                        "email":
                            email.strip(),

                        "language":
                            language.strip(),

                        "guide_type":
                            guide_type,

                        "experience_years":
                            experience_years,

                        "status":
                            status,

                        "notes":
                            notes.strip()
                    }

                    st.session_state.guides.append(
                        new_guide
                    )

                    st.session_state.next_guide_id += 1

                    st.success(
                        f"Đã thêm hướng dẫn viên: "
                        f"{full_name}"
                    )

                    st.rerun()

    # ========================================================
    # DANH SÁCH HDV
    # ========================================================

    with tab2:

        guides = st.session_state.guides

        if not guides:

            st.info(
                "Chưa có hướng dẫn viên."
            )

        else:

            display_data = []

            for guide in guides:

                display_data.append({
                    "ID":
                        guide["id"],

                    "Họ tên":
                        guide["full_name"],

                    "Điện thoại":
                        guide["phone"],

                    "Email":
                        guide["email"],

                    "Ngoại ngữ":
                        guide["language"],

                    "Loại HDV":
                        guide["guide_type"],

                    "Kinh nghiệm":
                        f"{guide['experience_years']} năm",

                    "Trạng thái":
                        guide["status"]
                })

            st.dataframe(
                display_data,
                use_container_width=True,
                hide_index=True
            )

            st.divider()

            st.subheader(
                "✏️ Chỉnh sửa / Xóa hướng dẫn viên"
            )

            guide_options = {
                f"{g['id']} - {g['full_name']}":
                    g["id"]
                for g in guides
            }

            selected_name = st.selectbox(
                "Chọn hướng dẫn viên",
                list(guide_options.keys())
            )

            selected_id = guide_options[
                selected_name
            ]

            selected_guide = get_guide(
                selected_id
            )

            if selected_guide:

                with st.form(
                    "edit_guide_form"
                ):

                    col1, col2 = st.columns(2)

                    with col1:

                        edit_name = st.text_input(
                            "Họ và tên",
                            value=selected_guide[
                                "full_name"
                            ]
                        )

                        edit_phone = st.text_input(
                            "Số điện thoại",
                            value=selected_guide[
                                "phone"
                            ]
                        )

                        edit_email = st.text_input(
                            "Email",
                            value=selected_guide[
                                "email"
                            ]
                        )

                        edit_language = st.text_input(
                            "Ngoại ngữ",
                            value=selected_guide[
                                "language"
                            ]
                        )

                    with col2:

                        type_options = [
                            "HDV nội địa",
                            "HDV quốc tế",
                            "HDV theo đoàn",
                            "HDV tự do"
                        ]

                        current_type = (
                            selected_guide[
                                "guide_type"
                            ]
                        )

                        type_index = (
                            type_options.index(
                                current_type
                            )
                            if current_type
                            in type_options
                            else 0
                        )

                        edit_type = st.selectbox(
                            "Loại HDV",
                            type_options,
                            index=type_index
                        )

                        edit_experience = (
                            st.number_input(
                                "Số năm kinh nghiệm",
                                min_value=0,
                                max_value=50,
                                value=int(
                                    selected_guide[
                                        "experience_years"
                                    ]
                                )
                            )
                        )

                        status_options = [
                            "Đang hoạt động",
                            "Tạm nghỉ",
                            "Nghỉ việc"
                        ]

                        current_status = (
                            selected_guide[
                                "status"
                            ]
                        )

                        status_index = (
                            status_options.index(
                                current_status
                            )
                            if current_status
                            in status_options
                            else 0
                        )

                        edit_status = st.selectbox(
                            "Trạng thái",
                            status_options,
                            index=status_index
                        )

                        edit_notes = st.text_area(
                            "Ghi chú",
                            value=selected_guide[
                                "notes"
                            ]
                        )

                    save = st.form_submit_button(
                        "💾 Lưu thay đổi",
                        use_container_width=True
                    )

                    if save:

                        if not edit_name.strip():

                            st.error(
                                "Họ tên không được để trống."
                            )

                        else:

                            selected_guide[
                                "full_name"
                            ] = edit_name.strip()

                            selected_guide[
                                "phone"
                            ] = edit_phone.strip()

                            selected_guide[
                                "email"
                            ] = edit_email.strip()

                            selected_guide[
                                "language"
                            ] = edit_language.strip()

                            selected_guide[
                                "guide_type"
                            ] = edit_type

                            selected_guide[
                                "experience_years"
                            ] = edit_experience

                            selected_guide[
                                "status"
                            ] = edit_status

                            selected_guide[
                                "notes"
                            ] = edit_notes.strip()

                            st.success(
                                "Đã cập nhật thông tin."
                            )

                            st.rerun()

                st.warning(
                    "⚠️ Xóa hướng dẫn viên sẽ xóa "
                    "cả các ca và ngày nghỉ liên quan."
                )

                if st.button(
                    "🗑️ Xóa hướng dẫn viên",
                    type="secondary"
                ):

                    st.session_state.guides = [
                        g
                        for g
                        in st.session_state.guides
                        if g["id"] != selected_id
                    ]

                    st.session_state.shifts = [
                        s
                        for s
                        in st.session_state.shifts
                        if s["guide_id"] != selected_id
                    ]

                    st.session_state.days_off = [
                        d
                        for d
                        in st.session_state.days_off
                        if d["guide_id"] != selected_id
                    ]

                    st.success(
                        "Đã xóa hướng dẫn viên."
                    )

                    st.rerun()


# ============================================================
# XẾP CA THEO NGÀY
# ============================================================

elif menu == "📅 Xếp ca theo ngày":

    st.markdown(
        '<div class="main-title">'
        '📅 Xếp ca hướng dẫn viên'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">'
        'Phân công hướng dẫn viên cho từng tour '
        'theo ngày và thời gian'
        '</div>',
        unsafe_allow_html=True
    )

    guides = get_active_guides()

    if not guides:

        st.warning(
            "Chưa có hướng dẫn viên đang hoạt động. "
            "Hãy thêm hướng dẫn viên trước."
        )

    else:

        guide_options = {
            f"{g['full_name']} | {g['guide_type']}":
                g["id"]
            for g in guides
        }

        with st.form("add_shift_form"):

            st.subheader(
                "Thông tin phân ca"
            )

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
                    placeholder=(
                        "VD: Tour Vũng Tàu 1 ngày"
                    )
                )

                destination = st.text_input(
                    "Điểm đến",
                    placeholder=(
                        "VD: Bạch Dinh - Tượng Chúa "
                        "Kitô - Bãi Sau"
                    )
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
                    placeholder=(
                        "VD: Khách sạn ABC"
                    )
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

                    st.error(
                        "Vui lòng nhập tên tour."
                    )

                elif end_time <= start_time:

                    st.error(
                        "Giờ kết thúc phải lớn hơn "
                        "giờ bắt đầu."
                    )

                elif is_day_off(
                    selected_guide_id,
                    shift_date
                ):

                    st.error(
                        "❌ Hướng dẫn viên này đã đăng ký "
                        f"nghỉ ngày "
                        f"{format_date(shift_date)}."
                    )

                else:

                    conflict = check_shift_conflict(
                        selected_guide_id,
                        shift_date,
                        start_time,
                        end_time
                    )

                    if conflict:

                        guide = get_guide(
                            selected_guide_id
                        )

                        st.error(
                            "❌ Hướng dẫn viên đã có ca "
                            "bị trùng giờ."
                        )

                        st.warning(
                            f"HDV: "
                            f"{guide['full_name']}\n\n"
                            f"Ca hiện tại: "
                            f"{format_time(conflict['start_time'])}"
                            f" - "
                            f"{format_time(conflict['end_time'])}"
                            f"\n\n"
                            f"Tour: "
                            f"{conflict['tour_name']}"
                        )

                    else:

                        new_shift = {
                            "id":
                                st.session_state.next_shift_id,

                            "guide_id":
                                selected_guide_id,

                            "shift_date":
                                shift_date,

                            "start_time":
                                start_time,

                            "end_time":
                                end_time,

                            "tour_name":
                                tour_name.strip(),

                            "destination":
                                destination.strip(),

                            "tour_type":
                                tour_type,

                            "guest_count":
                                guest_count,

                            "pickup_location":
                                pickup_location.strip(),

                            "status":
                                status,

                            "notes":
                                notes.strip()
                        }

                        st.session_state.shifts.append(
                            new_shift
                        )

                        st.session_state.next_shift_id += 1

                        st.success(
                            "✅ Đã xếp ca thành công!"
                        )

                        st.rerun()


# ============================================================
# LỊCH LÀM VIỆC
# ============================================================

elif menu == "🗓️ Lịch làm việc":

    st.markdown(
        '<div class="main-title">'
        '🗓️ Lịch làm việc'
        '</div>',
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

    with col3:

        guide_filter_options = {
            "Tất cả hướng dẫn viên": None
        }

        for guide in st.session_state.guides:

            guide_filter_options[
                guide["full_name"]
            ] = guide["id"]

        selected_guide_filter = st.selectbox(
            "Hướng dẫn viên",
            list(guide_filter_options.keys())
        )

    if from_date > to_date:

        st.error(
            "Ngày bắt đầu không được lớn hơn ngày kết thúc."
        )

    else:

        selected_guide_id = guide_filter_options[
            selected_guide_filter
        ]

        filtered_shifts = []

        for shift in st.session_state.shifts:

            if not (
                from_date
                <= shift["shift_date"]
                <= to_date
            ):
                continue

            if (
                selected_guide_id is not None
                and shift["guide_id"]
                != selected_guide_id
            ):
                continue

            filtered_shifts.append(
                shift
            )

        filtered_shifts.sort(
            key=lambda x: (
                x["shift_date"],
                x["start_time"]
            )
        )

        st.write(
            f"**Tổng số ca:** "
            f"{len(filtered_shifts)}"
        )

        if not filtered_shifts:

            st.info(
                "Không có ca trong khoảng thời gian này."
            )

        else:

            display_data = []

            for shift in filtered_shifts:

                guide = get_guide(
                    shift["guide_id"]
                )

                display_data.append({
                    "Ngày":
                        format_date(
                            shift["shift_date"]
                        ),

                    "HDV":
                        guide["full_name"]
                        if guide
                        else "Không xác định",

                    "Giờ":
                        f"{format_time(shift['start_time'])}"
                        f" - "
                        f"{format_time(shift['end_time'])}",

                    "Tour":
                        shift["tour_name"],

                    "Điểm đến":
                        shift["destination"],

                    "Loại tour":
                        shift["tour_type"],

                    "Số khách":
                        shift["guest_count"],

                    "Điểm đón":
                        shift["pickup_location"],

                    "Trạng thái":
                        shift["status"]
                })

            st.dataframe(
                display_data,
                use_container_width=True,
                hide_index=True
            )

            st.divider()

            st.subheader(
                "📌 Chi tiết từng ca"
            )

            for shift in filtered_shifts:

                guide = get_guide(
                    shift["guide_id"]
                )

                guide_name = (
                    guide["full_name"]
                    if guide
                    else "Không xác định"
                )

                with st.expander(
                    f"{format_date(shift['shift_date'])}"
                    f" | {guide_name}"
                    f" | {shift['tour_name']}"
                ):

                    c1, c2, c3 = st.columns(3)

                    c1.write(
                        f"**HDV:** {guide_name}"
                    )

                    c2.write(
                        f"**Thời gian:** "
                        f"{format_time(shift['start_time'])}"
                        f" - "
                        f"{format_time(shift['end_time'])}"
                    )

                    c3.write(
                        f"**Số khách:** "
                        f"{shift['guest_count']}"
                    )

                    st.write(
                        f"**Điểm đến:** "
                        f"{shift['destination']}"
                    )

                    st.write(
                        f"**Điểm đón:** "
                        f"{shift['pickup_location']}"
                    )

                    st.write(
                        f"**Loại tour:** "
                        f"{shift['tour_type']}"
                    )

                    st.write(
                        f"**Trạng thái:** "
                        f"{shift['status']}"
                    )

                    if shift["notes"]:

                        st.write(
                            f"**Ghi chú:** "
                            f"{shift['notes']}"
                        )


# ============================================================
# NGÀY NGHỈ
# ============================================================

elif menu == "🏖️ Ngày nghỉ":

    st.markdown(
        '<div class="main-title">'
        '🏖️ Quản lý ngày nghỉ'
        '</div>',
        unsafe_allow_html=True
    )

    guides = st.session_state.guides

    if not guides:

        st.info(
            "Chưa có hướng dẫn viên."
        )

    else:

        tab1, tab2 = st.tabs([
            "➕ Đăng ký ngày nghỉ",
            "📋 Danh sách ngày nghỉ"
        ])

        # ----------------------------------------------------
        # THÊM NGÀY NGHỈ
        # ----------------------------------------------------

        with tab1:

            guide_options = {
                guide["full_name"]:
                    guide["id"]
                for guide in guides
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
                    placeholder=(
                        "VD: Nghỉ phép, việc cá nhân..."
                    )
                )

                submit_off = st.form_submit_button(
                    "🏖️ Đăng ký ngày nghỉ",
                    use_container_width=True
                )

                if submit_off:

                    guide_id = guide_options[
                        selected_guide
                    ]

                    if is_day_off(
                        guide_id,
                        off_date
                    ):

                        st.error(
                            "Hướng dẫn viên đã đăng ký "
                            "nghỉ ngày này."
                        )

                    else:

                        new_day_off = {
                            "id":
                                st.session_state.next_dayoff_id,

                            "guide_id":
                                guide_id,

                            "off_date":
                                off_date,

                            "reason":
                                reason.strip()
                        }

                        st.session_state.days_off.append(
                            new_day_off
                        )

                        st.session_state.next_dayoff_id += 1

                        st.success(
                            "Đã đăng ký ngày nghỉ."
                        )

                        st.rerun()

        # ----------------------------------------------------
        # DANH SÁCH NGÀY NGHỈ
        # ----------------------------------------------------

        with tab2:

            days_off = sorted(
                st.session_state.days_off,
                key=lambda x: x["off_date"],
                reverse=True
            )

            if not days_off:

                st.info(
                    "Chưa có ngày nghỉ nào."
                )

            else:

                for item in days_off:

                    guide = get_guide(
                        item["guide_id"]
                    )

                    guide_name = (
                        guide["full_name"]
                        if guide
                        else "Không xác định"
                    )

                    c1, c2, c3, c4 = st.columns([
                        2, 2, 4, 1
                    ])

                    c1.write(
                        f"**{guide_name}**"
                    )

                    c2.write(
                        format_date(
                            item["off_date"]
                        )
                    )

                    c3.write(
                        item["reason"]
                    )

                    if c4.button(
                        "🗑️",
                        key=f"delete_off_{item['id']}"
                    ):

                        st.session_state.days_off = [
                            d
                            for d
                            in st.session_state.days_off
                            if d["id"]
                            != item["id"]
                        ]

                        st.success(
                            "Đã xóa ngày nghỉ."
                        )

                        st.rerun()


# ============================================================
# QUẢN LÝ CA
# ============================================================

elif menu == "⚙️ Quản lý ca":

    st.markdown(
        '<div class="main-title">'
        '⚙️ Quản lý ca'
        '</div>',
        unsafe_allow_html=True
    )

    shifts = sorted(
        st.session_state.shifts,
        key=lambda x: (
            x["shift_date"],
            x["start_time"]
        )
    )

    if not shifts:

        st.info(
            "Chưa có ca nào."
        )

    else:

        shift_options = {}

        for shift in shifts:

            guide = get_guide(
                shift["guide_id"]
            )

            guide_name = (
                guide["full_name"]
                if guide
                else "Không xác định"
            )

            shift_options[
                f"#{shift['id']} | "
                f"{format_date(shift['shift_date'])} | "
                f"{guide_name} | "
                f"{shift['tour_name']}"
            ] = shift["id"]

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

            guide_options = {
                f"{g['id']} - {g['full_name']}":
                    g["id"]
                for g in st.session_state.guides
            }

            current_guide_text = next(
                (
                    key
                    for key, value
                    in guide_options.items()
                    if value
                    == selected_shift["guide_id"]
                ),
                list(
                    guide_options.keys()
                )[0]
            )

            with st.form(
                "edit_shift_form"
            ):

                col1, col2 = st.columns(2)

                with col1:

                    edit_guide_text = st.selectbox(
                        "Hướng dẫn viên",
                        list(
                            guide_options.keys()
                        ),
                        index=list(
                            guide_options.keys()
                        ).index(
                            current_guide_text
                        )
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
                        value=selected_shift[
                            "start_time"
                        ]
                    )

                    edit_end = st.time_input(
                        "Giờ kết thúc",
                        value=selected_shift[
                            "end_time"
                        ]
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
                        ]
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

                    current_tour_type = (
                        selected_shift[
                            "tour_type"
                        ]
                    )

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

                    edit_guest_count = (
                        st.number_input(
                            "Số khách",
                            min_value=0,
                            max_value=10000,
                            value=int(
                                selected_shift[
                                    "guest_count"
                                ]
                            )
                        )
                    )

                    edit_pickup = st.text_input(
                        "Điểm đón",
                        value=selected_shift[
                            "pickup_location"
                        ]
                    )

                    status_options = [
                        "Đã xếp",
                        "Đang thực hiện",
                        "Hoàn thành",
                        "Đã hủy"
                    ]

                    current_status = (
                        selected_shift[
                            "status"
                        ]
                    )

                    status_index = (
                        status_options.index(
                            current_status
                        )
                        if current_status
                        in status_options
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
                    ]
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
                            exclude_shift_id=(
                                selected_shift_id
                            )
                        )

                        if conflict:

                            st.error(
                                "❌ Ca mới bị trùng với ca khác."
                            )

                            st.warning(
                                f"Tour trùng: "
                                f"{conflict['tour_name']} | "
                                f"{format_time(conflict['start_time'])}"
                                f" - "
                                f"{format_time(conflict['end_time'])}"
                            )

                        else:

                            selected_shift[
                                "guide_id"
                            ] = edit_guide_id

                            selected_shift[
                                "shift_date"
                            ] = edit_date

                            selected_shift[
                                "start_time"
                            ] = edit_start

                            selected_shift[
                                "end_time"
                            ] = edit_end

                            selected_shift[
                                "tour_name"
                            ] = edit_tour.strip()

                            selected_shift[
                                "destination"
                            ] = edit_destination.strip()

                            selected_shift[
                                "tour_type"
                            ] = edit_tour_type

                            selected_shift[
                                "guest_count"
                            ] = edit_guest_count

                            selected_shift[
                                "pickup_location"
                            ] = edit_pickup.strip()

                            selected_shift[
                                "status"
                            ] = edit_status

                            selected_shift[
                                "notes"
                            ] = edit_notes.strip()

                            st.success(
                                "Đã cập nhật ca."
                            )

                            st.rerun()

            st.divider()

            if st.button(
                "🗑️ Xóa ca này",
                type="secondary"
            ):

                st.session_state.shifts = [
                    shift
                    for shift
                    in st.session_state.shifts
                    if shift["id"]
                    != selected_shift_id
                ]

                st.success(
                    "Đã xóa ca."
                )

                st.rerun()
