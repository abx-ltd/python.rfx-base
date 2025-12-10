"""
Database triggers for rfx_client schema
"""

from alembic_utils.pg_trigger import PGTrigger
from alembic_utils.pg_function import PGFunction
from rfx_base import config

fn_update_pwp_date_complete = PGFunction(
    schema=config.RFX_CLIENT_SCHEMA,
    signature="fn_update_pwp_date_complete()",
    definition=f"""
    RETURNS TRIGGER 
    LANGUAGE plpgsql
    AS $function$
BEGIN
    -- Nếu Status đổi thành DONE và trước đó chưa DONE -> Gán thời gian hiện tại
    IF NEW.status = 'DONE'::{config.RFX_CLIENT_SCHEMA}.workpackageenum 
       AND (OLD.status IS DISTINCT FROM 'DONE'::{config.RFX_CLIENT_SCHEMA}.workpackageenum) THEN
        NEW.date_complete := NOW();
        
    -- (Tuỳ chọn) Nếu chuyển từ DONE ngược lại TODO -> Xóa ngày hoàn thành
    ELSIF NEW.status != 'DONE'::{config.RFX_CLIENT_SCHEMA}.workpackageenum THEN
        NEW.date_complete := NULL;
    END IF;

    RETURN NEW;
END;
$function$
    """,
)

fn_update_org_credit_balance = PGFunction(
    schema=config.RFX_CLIENT_SCHEMA,
    signature="fn_update_org_credit_balance()",
    definition=f"""
    RETURNS TRIGGER 
    LANGUAGE plpgsql
    AS $function$
DECLARE
    v_credit_amount NUMERIC(12, 2) := 0;
    v_ar_amount NUMERIC(12, 2) := 0;
    v_de_amount NUMERIC(12, 2) := 0;
    v_op_amount NUMERIC(12, 2) := 0;
    v_org_id UUID;
    v_project_id UUID;
BEGIN
    -- 1. Xác định Project ID và Organization ID
    v_project_id := COALESCE(NEW.project_id, OLD.project_id);
    
    SELECT organization_id INTO v_org_id 
    FROM {config.RFX_CLIENT_SCHEMA}.project 
    WHERE _id = v_project_id;

    -- Nếu không tìm thấy Org thì dừng (tránh lỗi)
    IF v_org_id IS NULL THEN
        RAISE NOTICE 'Không tìm thấy Organization cho Project %', v_project_id;
        RETURN NEW;
    END IF;

    -- 2. Tính toán Credit (Dựa trên công thức của View _organization_weekly_credit_usage)
    -- Chúng ta tính tổng cho Gói Work Package đang được tác động (NEW._id hoặc OLD._id)
    SELECT 
        -- Tổng Credit Amount
        COALESCE(SUM(
            (
                (EXTRACT(DAY FROM COALESCE(pwi.estimate, '00:00:00'::interval)) * 8::numeric) 
                + EXTRACT(HOUR FROM COALESCE(pwi.estimate, '00:00:00'::interval)) 
                + (EXTRACT(MINUTE FROM COALESCE(pwi.estimate, '00:00:00'::interval)) / 60.0)
            ) 
            * pwi.credit_per_unit 
            * COALESCE(NEW.quantity, 1)::numeric
        ), 0),

        -- AR Credits
        COALESCE(SUM(CASE WHEN pwi.type::text = 'ARCHITECTURE' THEN 
            (
                (EXTRACT(DAY FROM COALESCE(pwi.estimate, '00:00:00'::interval)) * 8::numeric) 
                + EXTRACT(HOUR FROM COALESCE(pwi.estimate, '00:00:00'::interval)) 
                + (EXTRACT(MINUTE FROM COALESCE(pwi.estimate, '00:00:00'::interval)) / 60.0)
            ) * pwi.credit_per_unit * COALESCE(NEW.quantity, 1)::numeric
        ELSE 0 END), 0),

        -- DE Credits
        COALESCE(SUM(CASE WHEN pwi.type::text = 'DEVELOPMENT' THEN 
            (
                (EXTRACT(DAY FROM COALESCE(pwi.estimate, '00:00:00'::interval)) * 8::numeric) 
                + EXTRACT(HOUR FROM COALESCE(pwi.estimate, '00:00:00'::interval)) 
                + (EXTRACT(MINUTE FROM COALESCE(pwi.estimate, '00:00:00'::interval)) / 60.0)
            ) * pwi.credit_per_unit * COALESCE(NEW.quantity, 1)::numeric
        ELSE 0 END), 0),

        -- OP Credits
        COALESCE(SUM(CASE WHEN pwi.type::text = 'OPERATION' THEN 
            (
                (EXTRACT(DAY FROM COALESCE(pwi.estimate, '00:00:00'::interval)) * 8::numeric) 
                + EXTRACT(HOUR FROM COALESCE(pwi.estimate, '00:00:00'::interval)) 
                + (EXTRACT(MINUTE FROM COALESCE(pwi.estimate, '00:00:00'::interval)) / 60.0)
            ) * pwi.credit_per_unit * COALESCE(NEW.quantity, 1)::numeric
        ELSE 0 END), 0)

    INTO v_credit_amount, v_ar_amount, v_de_amount, v_op_amount
    FROM {config.RFX_CLIENT_SCHEMA}.project_work_package_work_item pwpwi
    JOIN {config.RFX_CLIENT_SCHEMA}.project_work_item pwi ON pwpwi.project_work_item_id = pwi._id
    WHERE pwpwi.project_work_package_id = COALESCE(NEW._id, OLD._id)
      AND pwpwi._deleted IS NULL
      AND pwi._deleted IS NULL;

    -- Debug Log (để kiểm tra khi chạy)
    RAISE NOTICE 'Org: %, Total: %, AR: %, DE: %, OP: %', v_org_id, v_credit_amount, v_ar_amount, v_de_amount, v_op_amount;

    -- 3. Cập nhật bảng credit_balance
    
    -- TRƯỜNG HỢP 1: Chuyển sang DONE (Trừ tiền)
    -- So sánh status dưới dạng text để an toàn
    IF (OLD.status::text != 'DONE' AND NEW.status::text = 'DONE') THEN
        UPDATE {config.RFX_CLIENT_SCHEMA}.credit_balance
        SET 
            total_credits = total_credits - v_credit_amount, -- Trừ số dư khả dụng
            total_used    = total_used    + v_credit_amount, -- Tăng số đã dùng
            ar_credits    = ar_credits    - v_ar_amount,
            de_credits    = de_credits    - v_de_amount,
            op_credits    = op_credits    - v_op_amount,
            last_usage_date = NOW(),
            _updated = NOW()
        WHERE organization_id = v_org_id;

    -- TRƯỜNG HỢP 2: Chuyển từ DONE sang trạng thái khác (Undo - Hoàn tiền)
    ELSIF (OLD.status::text = 'DONE' AND NEW.status::text != 'DONE') THEN
        UPDATE {config.RFX_CLIENT_SCHEMA}.credit_balance
        SET 
            total_credits = total_credits + v_credit_amount, -- Cộng lại số dư
            total_used    = total_used    - v_credit_amount, -- Giảm số đã dùng
            ar_credits    = ar_credits    + v_ar_amount,
            de_credits    = de_credits    + v_de_amount,
            op_credits    = op_credits    + v_op_amount,
            _updated = NOW()
        WHERE organization_id = v_org_id;
    END IF;

    RETURN NEW;
END;
$function$
    """,
)

trg_pwp_auto_date_complete = PGTrigger(
    schema=config.RFX_CLIENT_SCHEMA,
    signature="trg_pwp_auto_date_complete",
    on_entity=f"{config.RFX_CLIENT_SCHEMA}.project_work_package",
    is_constraint=False,
    definition=f"""
        BEFORE UPDATE ON {config.RFX_CLIENT_SCHEMA}.project_work_package
        FOR EACH ROW
        EXECUTE FUNCTION {config.RFX_CLIENT_SCHEMA}.fn_update_pwp_date_complete()
    """,
)

trg_auto_update_credit_balance = PGTrigger(
    schema=config.RFX_CLIENT_SCHEMA,
    signature="trg_auto_update_credit_balance",
    on_entity=f"{config.RFX_CLIENT_SCHEMA}.project_work_package",
    is_constraint=False,
    definition=f"""
        AFTER UPDATE OF status ON {config.RFX_CLIENT_SCHEMA}.project_work_package
        FOR EACH ROW
        EXECUTE FUNCTION {config.RFX_CLIENT_SCHEMA}.fn_update_org_credit_balance()
    """,
)
