import streamlit as st
from supabase import create_client, Client


# ============================================================
# 페이지 설정
# ============================================================

st.set_page_config(
    page_title="택배 배송 앱",
    page_icon="🚚",
    layout="wide",
)


# ============================================================
# Supabase
# ============================================================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]


def get_supabase() -> Client:
    return create_client(
        SUPABASE_URL,
        SUPABASE_KEY,
    )


# 세션별 Supabase 클라이언트
if "supabase" not in st.session_state:
    st.session_state.supabase = get_supabase()

supabase = st.session_state.supabase


# ============================================================
# 세션 상태
# ============================================================

if "user" not in st.session_state:
    st.session_state.user = None

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "remember_me" not in st.session_state:
    st.session_state.remember_me = True


# ============================================================
# 사용자 확인
# ============================================================

def is_owner(user):
    if user is None:
        return False

    email = (
        getattr(user, "email", None) or ""
    ).lower()

    return "owner" in email


# ============================================================
# 로그아웃
# ============================================================

def logout():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass

    st.session_state.user = None
    st.session_state.logged_in = False

    st.rerun()


# ============================================================
# 로그인
# ============================================================

def login(email, password, remember_me):
    try:
        response = supabase.auth.sign_in_with_password(
            email=email,
            password=password,
        )

        user = response.user

        if user is None:
            st.error("로그인에 실패했습니다.")
            return

        st.session_state.user = user
        st.session_state.logged_in = True
        st.session_state.remember_me = remember_me

        st.rerun()

    except Exception as e:
        st.error(f"로그인 실패\n\n{e}")


# ============================================================
# 로그인 화면
# ============================================================

def login_page():

    st.title("🚚 택배 배송 앱")

    st.write("")

    col1, col2, col3 = st.columns(
        [1, 2, 1]
    )

    with col2:

        st.subheader("로그인")

        email = st.text_input(
            "이메일",
            placeholder="이메일을 입력하세요",
        )

        password = st.text_input(
            "비밀번호",
            type="password",
            placeholder="비밀번호를 입력하세요",
        )

        remember_me = st.checkbox(
            "로그인 유지",
            value=True,
        )

        if st.button(
            "로그인",
            type="primary",
            use_container_width=True,
        ):

            if not email.strip():
                st.warning("이메일을 입력해주세요.")
                return

            if not password:
                st.warning("비밀번호를 입력해주세요.")
                return

            login(
                email.strip(),
                password,
                remember_me,
            )


# ============================================================
# 비밀번호 변경
# ============================================================

def password_change_page():

    st.subheader("🔐 비밀번호 변경")

    current_password = st.text_input(
        "현재 비밀번호",
        type="password",
    )

    new_password = st.text_input(
        "새 비밀번호",
        type="password",
    )

    new_password_confirm = st.text_input(
        "새 비밀번호 확인",
        type="password",
    )

    if st.button(
        "비밀번호 변경",
        type="primary",
    ):

        if not current_password:
            st.warning("현재 비밀번호를 입력해주세요.")
            return

        if not new_password:
            st.warning("새 비밀번호를 입력해주세요.")
            return

        if len(new_password) < 6:
            st.warning(
                "비밀번호는 6자 이상으로 입력해주세요."
            )
            return

        if new_password != new_password_confirm:
            st.error(
                "새 비밀번호가 서로 다릅니다."
            )
            return

        user = st.session_state.user

        if user is None:
            st.error("로그인이 필요합니다.")
            return

        try:

            # 현재 비밀번호 확인
            supabase.auth.sign_in_with_password(
                email=user.email,
                password=current_password,
            )

            # 비밀번호 변경
            supabase.auth.update_user(
                {
                    "password": new_password
                }
            )

            st.success(
                "비밀번호가 변경되었습니다."
            )

        except Exception as e:

            st.error(
                f"비밀번호 변경 실패\n\n{e}"
            )


# ============================================================
# 고객 주소 저장
# ============================================================

def save_address(address):

    user = st.session_state.user

    if user is None:
        return False

    address = address.strip()

    if not address:
        return False

    try:

        supabase.auth.update_user(
            {
                "data": {
                    "saved_address": address
                }
            }
        )

        # 사용자 정보 다시 가져오기
        response = supabase.auth.get_user()

        if response.user is not None:
            st.session_state.user = response.user

        return True

    except Exception as e:

        st.error(
            f"주소 저장 실패\n\n{e}"
        )

        return False


# ============================================================
# 저장된 주소 가져오기
# ============================================================

def get_saved_address():

    user = st.session_state.user

    if user is None:
        return ""

    try:

        metadata = user.user_metadata or {}

        return (
            metadata.get("saved_address")
            or ""
        )

    except Exception:
        return ""


# ============================================================
# 고객 주문 생성
# ============================================================

def create_order(
    store_name,
    store_address,
    menu,
    address,
    save_address_check,
):

    user = st.session_state.user

    if user is None:
        st.error("로그인이 필요합니다.")
        return

    store_name = store_name.strip()
    store_address = store_address.strip()
    menu = menu.strip()
    address = address.strip()

    if not store_name:
        st.warning("마트명을 입력해주세요.")
        return

    if not store_address:
        st.warning("마트주소를 입력해주세요.")
        return

    if not menu:
        st.warning("물품을 입력해주세요.")
        return

    if not address:
        st.warning("배달주소를 입력해주세요.")
        return

    try:

        supabase.table("orders").insert(
            {
                "user_id": user.id,
                "store_name": store_name,
                "store_address": store_address,
                "menu": menu,
                "address": address,
                "status": "접수 대기",
                "estimated_time": None,
                "delivery_fee": None,
                "delay_message": None,
            }
        ).execute()

        if save_address_check:
            save_address(address)

        st.success(
            "배송 신청이 접수되었습니다."
        )

        st.rerun()

    except Exception as e:

        st.error(
            f"배송 신청 실패\n\n{e}"
        )


# ============================================================
# 고객 주문 목록
# ============================================================

def get_my_orders():

    user = st.session_state.user

    if user is None:
        return []

    try:

        response = (
            supabase
            .table("orders")
            .select("*")
            .eq("user_id", user.id)
            .order(
                "created_at",
                desc=True,
            )
            .execute()
        )

        return response.data or []

    except Exception as e:

        st.error(
            f"주문을 불러오지 못했습니다.\n\n{e}"
        )

        return []


# ============================================================
# 고객 - 받음 확인
# ============================================================

def confirm_received(order_id):

    try:

        supabase.table("orders").update(
            {
                "status": "최종 완료"
            }
        ).eq(
            "id",
            order_id,
        ).execute()

        st.success(
            "받음 확인이 완료되었습니다."
        )

        st.rerun()

    except Exception as e:

        st.error(
            f"받음 확인 실패\n\n{e}"
        )


# ============================================================
# 고객 화면
# ============================================================

def customer_page():

    user = st.session_state.user

    email = (
        user.email
        if user and user.email
        else "사용자"
    )

    st.title("🚚 고객 배송 신청")

    # --------------------------------------------------------
    # 상단
    # --------------------------------------------------------

    col1, col2 = st.columns(
        [4, 1]
    )

    with col1:

        st.write(
            f"로그인: **{email}**"
        )

    with col2:

        if st.button(
            "로그아웃",
            use_container_width=True,
        ):
            logout()

    # --------------------------------------------------------
    # 메뉴
    # --------------------------------------------------------

    menu = st.tabs(
        [
            "📦 배송 신청",
            "📋 내 배송",
            "🔐 비밀번호 변경",
        ]
    )

    # ========================================================
    # 배송 신청
    # ========================================================

    with menu[0]:

        st.subheader("배송 신청")

        saved_address = get_saved_address()

        with st.form(
            "delivery_form"
        ):

            store_name = st.text_input(
                "마트명",
                placeholder="예: 이마트",
            )

            store_address = st.text_input(
                "마트주소",
                placeholder="예: 인천광역시 ...",
            )

            item = st.text_input(
                "물품",
                placeholder="예: 생필품",
            )

            address = st.text_input(
                "배달주소",
                value=saved_address,
                placeholder="배달받을 주소",
            )

            save_address_check = st.checkbox(
                "이 주소를 저장해서 다음에도 사용",
                value=True,
            )

            submitted = st.form_submit_button(
                "🚚 배송 신청",
                type="primary",
                use_container_width=True,
            )

            if submitted:

                create_order(
                    store_name,
                    store_address,
                    item,
                    address,
                    save_address_check,
                )

        # 저장된 주소 안내

        if saved_address:

            st.info(
                f"📍 저장된 주소: {saved_address}"
            )

            if st.button(
                "저장된 주소 삭제",
            ):

                try:

                    supabase.auth.update_user(
                        {
                            "data": {
                                "saved_address": None
                            }
                        }
                    )

                    response = (
                        supabase.auth.get_user()
                    )

                    if response.user:
                        st.session_state.user = (
                            response.user
                        )

                    st.success(
                        "저장된 주소를 삭제했습니다."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"주소 삭제 실패\n\n{e}"
                    )

    # ========================================================
    # 내 배송
    # ========================================================

    with menu[1]:

        st.subheader("📋 내 배송 현황")

        orders = get_my_orders()

        active_orders = [
            order
            for order in orders
            if order.get("status")
            in [
                "접수 대기",
                "배송 중",
                "배송 완료",
                "최종 완료",
            ]
        ]

        if not active_orders:

            st.info(
                "현재 배송 내역이 없습니다."
            )

        for order in active_orders:

            order_id = order.get("id")

            status = (
                order.get("status")
                or "알 수 없음"
            )

            store_name = (
                order.get("store_name")
                or ""
            )

            store_address = (
                order.get("store_address")
                or ""
            )

            item = (
                order.get("menu")
                or ""
            )

            address = (
                order.get("address")
                or ""
            )

            estimated = (
                order.get("estimated_time")
                or "준비 중"
            )

            fee = (
                order.get("delivery_fee")
                or "계산 중"
            )

            delay = (
                order.get("delay_message")
                or ""
            )

            # 상태 색상

            if status == "접수 대기":
                status_color = "🟠"

            elif status == "배송 중":
                status_color = "🔵"

            elif status == "배송 완료":
                status_color = "🟢"

            elif status == "최종 완료":
                status_color = "✅"

            else:
                status_color = "⚪"

            with st.container(
                border=True
            ):

                st.markdown(
                    f"### {status_color} {store_name}"
                )

                st.write(
                    f"**상태:** {status}"
                )

                st.write(
                    f"**마트주소:** {store_address}"
                )

                st.write(
                    f"**물품:** {item}"
                )

                st.write(
                    f"**배달주소:** {address}"
                )

                st.write(
                    f"**예정시간:** {estimated}"
                )

                st.write(
                    f"**배송요금:** {fee}"
                )

                if delay:

                    st.warning(
                        f"지연사유: {delay}"
                    )

                if status == "배송 완료":

                    if st.button(
                        "📦 받음 확인",
                        key=f"received_{order_id}",
                        type="primary",
                        use_container_width=True,
                    ):

                        confirm_received(
                            order_id
                        )

                elif status == "최종 완료":

                    st.success(
                        "배송이 최종 완료되었습니다."
                    )

    # ========================================================
    # 비밀번호 변경
    # ========================================================

    with menu[2]:

        password_change_page()


# ============================================================
# 관제탑 주문 가져오기
# ============================================================

def get_all_orders():

    try:

        response = (
            supabase
            .table("orders")
            .select("*")
            .order(
                "created_at",
                desc=True,
            )
            .execute()
        )

        return response.data or []

    except Exception as e:

        st.error(
            f"주문 목록을 불러오지 못했습니다.\n\n{e}"
        )

        return []


# ============================================================
# 배송 취소
# ============================================================

def cancel_order(order_id):

    try:

        supabase.table("orders").update(
            {
                "status": "배송 취소"
            }
        ).eq(
            "id",
            order_id,
        ).execute()

        st.success(
            "배송이 취소되었습니다."
        )

        st.rerun()

    except Exception as e:

        st.error(
            f"배송 취소 실패\n\n{e}"
        )


# ============================================================
# 배송 수락
# ============================================================

def accept_order(
    order_id,
    estimated_time,
    delivery_fee,
    delay_message,
):

    if not estimated_time.strip():

        st.warning(
            "예정시간을 입력해주세요."
        )

        return

    if not delivery_fee.strip():

        st.warning(
            "배송요금을 입력해주세요."
        )

        return

    try:

        supabase.table("orders").update(
            {
                "status": "배송 중",
                "estimated_time":
                    estimated_time.strip(),
                "delivery_fee":
                    delivery_fee.strip(),
                "delay_message":
                    delay_message.strip()
                    or None,
            }
        ).eq(
            "id",
            order_id,
        ).execute()

        st.success(
            "배송을 수락했습니다."
        )

        st.rerun()

    except Exception as e:

        st.error(
            f"배송 수락 실패\n\n{e}"
        )


# ============================================================
# 배송 완료
# ============================================================

def complete_order(order_id):

    try:

        supabase.table("orders").update(
            {
                "status": "배송 완료"
            }
        ).eq(
            "id",
            order_id,
        ).execute()

        st.success(
            "배송 완료 처리되었습니다."
        )

        st.rerun()

    except Exception as e:

        st.error(
            f"배송 완료 처리 실패\n\n{e}"
        )


# ============================================================
# 관제탑
# ============================================================

def owner_page():

    st.title("🚚 배송 관제탑")

    col1, col2 = st.columns(
        [4, 1]
    )

    with col1:

        st.write(
            "전체 배송 주문을 관리합니다."
        )

    with col2:

        if st.button(
            "로그아웃",
            use_container_width=True,
        ):
            logout()

    st.divider()

    orders = get_all_orders()

    active_orders = [
        order
        for order in orders
        if order.get("status")
        in [
            "접수 대기",
            "배송 중",
            "배송 완료",
        ]
    ]

    # --------------------------------------------------------
    # 통계
    # --------------------------------------------------------

    waiting_count = len(
        [
            order
            for order in active_orders
            if order.get("status")
            == "접수 대기"
        ]
    )

    delivering_count = len(
        [
            order
            for order in active_orders
            if order.get("status")
            == "배송 중"
        ]
    )

    completed_count = len(
        [
            order
            for order in active_orders
            if order.get("status")
            == "배송 완료"
        ]
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "접수 대기",
            waiting_count,
        )

    with c2:
        st.metric(
            "배송 중",
            delivering_count,
        )

    with c3:
        st.metric(
            "배송 완료",
            completed_count,
        )

    st.divider()

    # --------------------------------------------------------
    # 주문 없음
    # --------------------------------------------------------

    if not active_orders:

        st.info(
            "현재 처리할 배송이 없습니다."
        )

        return

    # --------------------------------------------------------
    # 주문 표시
    # --------------------------------------------------------

    for order in active_orders:

        order_id = order.get("id")

        status = (
            order.get("status")
            or "접수 대기"
        )

        user_id = (
            order.get("user_id")
            or ""
        )

        store_name = (
            order.get("store_name")
            or ""
        )

        store_address = (
            order.get("store_address")
            or ""
        )

        item = (
            order.get("menu")
            or ""
        )

        address = (
            order.get("address")
            or ""
        )

        estimated = (
            order.get("estimated_time")
            or ""
        )

        fee = (
            order.get("delivery_fee")
            or ""
        )

        delay = (
            order.get("delay_message")
            or ""
        )

        if status == "접수 대기":

            status_icon = "🟠"

        elif status == "배송 중":

            status_icon = "🔵"

        else:

            status_icon = "🟢"

        with st.container(
            border=True
        ):

            st.markdown(
                f"### {status_icon} {store_name}"
            )

            col1, col2 = st.columns(2)

            with col1:

                st.write(
                    f"**상태:** {status}"
                )

                st.write(
                    f"**신청자 ID:** {user_id}"
                )

                st.write(
                    f"**물품:** {item}"
                )

                st.write(
                    f"**마트주소:** {store_address}"
                )

            with col2:

                st.write(
                    f"**배달주소:** {address}"
                )

                st.write(
                    f"**예정시간:** "
                    f"{estimated or '대기'}"
                )

                st.write(
                    f"**배송요금:** "
                    f"{fee or '대기'}"
                )

                if delay:

                    st.warning(
                        f"지연사유: {delay}"
                    )

            st.divider()

            # =================================================
            # 접수 대기
            # =================================================

            if status == "접수 대기":

                st.write(
                    "### 배송 지정"
                )

                c1, c2 = st.columns(2)

                with c1:

                    estimated_input = st.text_input(
                        "예정시간",
                        value="18시 30분까지",
                        key=f"estimated_{order_id}",
                    )

                with c2:

                    fee_input = st.text_input(
                        "배송요금",
                        value="3000원",
                        key=f"fee_{order_id}",
                    )

                delay_input = st.text_input(
                    "지연사유",
                    placeholder="없으면 비워두세요",
                    key=f"delay_{order_id}",
                )

                c1, c2 = st.columns(2)

                with c1:

                    if st.button(
                        "❌ 배송 취소",
                        key=f"cancel_{order_id}",
                        use_container_width=True,
                    ):

                        cancel_order(
                            order_id
                        )

                with c2:

                    if st.button(
                        "✅ 배송 수락",
                        key=f"accept_{order_id}",
                        type="primary",
                        use_container_width=True,
                    ):

                        accept_order(
                            order_id,
                            estimated_input,
                            fee_input,
                            delay_input,
                        )

            # =================================================
            # 배송 중
            # =================================================

            elif status == "배송 중":

                c1, c2 = st.columns(2)

                with c1:

                    if st.button(
                        "❌ 배송 취소",
                        key=f"cancel_delivery_{order_id}",
                        use_container_width=True,
                    ):

                        cancel_order(
                            order_id
                        )

                with c2:

                    if st.button(
                        "✅ 배송 완료",
                        key=f"complete_{order_id}",
                        type="primary",
                        use_container_width=True,
                    ):

                        complete_order(
                            order_id
                        )

            # =================================================
            # 배송 완료
            # =================================================

            elif status == "배송 완료":

                st.success(
                    "고객의 받음 확인을 기다리는 중입니다."
                )


# ============================================================
# 메인
# ============================================================

def main():

    # --------------------------------------------------------
    # 현재 로그인 세션 확인
    # --------------------------------------------------------

    if not st.session_state.logged_in:

        try:

            session = (
                supabase.auth.get_session()
            )

            if session is not None:

                user = (
                    getattr(
                        session,
                        "user",
                        None,
                    )
                )

                if user is not None:

                    st.session_state.user = user
                    st.session_state.logged_in = True

        except Exception:
            pass

    # --------------------------------------------------------
    # 로그인 안 되어 있으면 로그인 화면
    # --------------------------------------------------------

    if not st.session_state.logged_in:

        login_page()
        return

    # --------------------------------------------------------
    # 사용자
    # --------------------------------------------------------

    user = st.session_state.user

    if user is None:

        st.session_state.logged_in = False

        login_page()

        return

    # --------------------------------------------------------
    # 관제탑 / 고객 구분
    # --------------------------------------------------------

    if is_owner(user):

        owner_page()

    else:

        customer_page()


# ============================================================
# 실행
# ============================================================

if __name__ == "__main__":
    main()
