"""
德育管理 API - 獎懲登記、常規違紀、操行評估
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.conduct import RewardPunishment, RegularViolation, ConductAssessment
from app.models.student import Student, Class

router = APIRouter(prefix="/conduct", tags=["德育管理"])


# ============ 獎懲登記 ============

class RewardPunishmentCreate(BaseModel):
    student_id: int
    semester_id: int
    reward_type: Optional[str] = None
    reward_count: int = 0
    reward_reason: Optional[str] = None
    reward_date: Optional[date] = None
    punishment_type: Optional[str] = None
    punishment_count: int = 0
    punishment_reason: Optional[str] = None
    punishment_date: Optional[date] = None


@router.post("/register")
async def register_reward_punishment(
    data: RewardPunishmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """登記獎勵或懲罰"""
    student = db.query(Student).filter(Student.id == data.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="學生不存在")

    rp = RewardPunishment(
        student_id=data.student_id,
        semester_id=data.semester_id,
        reward_type=data.reward_type,
        reward_count=data.reward_count,
        reward_reason=data.reward_reason,
        reward_date=data.reward_date,
        punishment_type=data.punishment_type,
        punishment_count=data.punishment_count,
        punishment_reason=data.punishment_reason,
        punishment_date=data.punishment_date,
        created_by=current_user.id,
    )
    db.add(rp)
    db.commit()
    db.refresh(rp)

    return {"message": "登記成功", "id": rp.id}


# ============ 常規違紀登記 ============

class RegularViolationCreate(BaseModel):
    student_id: int
    class_id: int
    semester_id: int
    violation_type: str  # 欠作業/欠課本/上課違規/儀表不符/遲到/缺席/請假
    count: int = 0
    record_date: Optional[date] = None


@router.post("/violations")
async def register_violation(
    data: RegularViolationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """登記常規違紀"""
    student = db.query(Student).filter(Student.id == data.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="學生不存在")

    rv = RegularViolation(
        student_id=data.student_id,
        class_id=data.class_id,
        semester_id=data.semester_id,
        violation_type=data.violation_type,
        count=data.count,
        record_date=data.record_date,
        created_by=current_user.id,
    )
    db.add(rv)
    db.commit()
    db.refresh(rv)

    return {"message": "登記成功", "id": rv.id}


# ============ 操行評估 ============

class ConductAssessmentCreate(BaseModel):
    student_id: int
    semester_id: int
    fail_homework: int = 0
    fail_textbook: int = 0
    fail_classroom: int = 0
    fail_uniform: int = 0
    fail_late: int = 0
    fail_absent: int = 0
    leave_hours: int = 0
    before_rewards: int = 0
    before_minor_awards: int = 0
    before_major_awards: int = 0
    after_rewards: int = 0
    after_minor_awards: int = 0
    after_major_awards: int = 0
    volunteer_hours: float = 0
    max_assessment: Optional[str] = None
    previous_assessment: Optional[str] = None
    current_assessment: Optional[str] = None
    change: Optional[str] = None
    cumulative_fails: int = 0
    comment: Optional[str] = None


@router.post("/assessment")
async def save_conduct_assessment(
    data: ConductAssessmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """儲存操行評估"""
    student = db.query(Student).filter(Student.id == data.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="學生不存在")

    # 檢查是否已有記錄
    existing = db.query(ConductAssessment).filter(
        ConductAssessment.student_id == data.student_id,
        ConductAssessment.semester_id == data.semester_id,
    ).first()

    if existing:
        # 更新現有記錄
        for key, value in data.model_dump().items():
            setattr(existing, key, value)
        db.commit()
        return {"message": "更新成功", "id": existing.id}

    # 新增記錄
    ca = ConductAssessment(**data.model_dump(), created_by=current_user.id)
    db.add(ca)
    db.commit()
    db.refresh(ca)

    return {"message": "儲存成功", "id": ca.id}


# ============ 查詢 ============

@router.get("/class/{class_id}")
async def get_class_conduct(
    class_id: int,
    semester_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得班級的德育資料"""
    students = db.query(Student).filter(Student.class_id == class_id).order_by(Student.class_number).all()
    student_ids = [s.id for s in students]

    # 取得操行評估
    query = db.query(ConductAssessment).filter(ConductAssessment.student_id.in_(student_ids))
    if semester_id:
        query = query.filter(ConductAssessment.semester_id == semester_id)
    assessments = {a.student_id: a for a in query.all()}

    # 組裝資料
    result = []
    for student in students:
        ca = assessments.get(student.id)
        if ca:
            result.append({
                "student_no": student.student_no,
                "name": student.name,
                "class_number": student.class_number,
                "fail_homework": ca.fail_homework,
                "fail_textbook": ca.fail_textbook,
                "fail_classroom": ca.fail_classroom,
                "fail_uniform": ca.fail_uniform,
                "fail_late": ca.fail_late,
                "fail_absent": ca.fail_absent,
                "leave_hours": ca.leave_hours,
                "before_rewards": ca.before_rewards,
                "before_minor_awards": ca.before_minor_awards,
                "before_major_awards": ca.before_major_awards,
                "after_rewards": ca.after_rewards,
                "after_minor_awards": ca.after_minor_awards,
                "after_major_awards": ca.after_major_awards,
                "volunteer_hours": ca.volunteer_hours,
                "max_assessment": ca.max_assessment,
                "current_assessment": ca.current_assessment,
                "comment": ca.comment,
            })

    return result


@router.get("/rewards/{student_id}")
async def get_student_rewards(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得學生的獎懲記錄"""
    records = db.query(RewardPunishment).filter(
        RewardPunishment.student_id == student_id,
        RewardPunishment.is_active == True,
    ).all()

    return [
        {
            "id": r.id,
            "reward_type": r.reward_type,
            "reward_count": r.reward_count,
            "reward_reason": r.reward_reason,
            "reward_date": r.reward_date.isoformat() if r.reward_date else None,
            "punishment_type": r.punishment_type,
            "punishment_count": r.punishment_count,
            "punishment_reason": r.punishment_reason,
            "punishment_date": r.punishment_date.isoformat() if r.punishment_date else None,
        }
        for r in records
    ]


@router.post("/excel-import")
async def import_conduct_from_excel(
    file_path: str,
    class_id: int,
    semester_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """從 Excel 匯入操行資料"""
    import openpyxl

    try:
        wb = openpyxl.load_workbook(file_path)
        ws = wb.active

        imported = 0
        for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
            if not row[0]:
                continue

            class_number = row[0]  # 學號
            name = row[1] if len(row) > 1 else ""
            欠作業 = row[2] if len(row) > 2 else 0
            欠課本 = row[3] if len(row) > 3 else 0
            上課違規 = row[4] if len(row) > 4 else 0
            儀表不符 = row[5] if len(row) > 5 else 0
            遲到 = row[6] if len(row) > 6 else 0
            缺席 = row[7] if len(row) > 7 else 0
            請假 = row[8] if len(row) > 8 else 0
            before_rewards = row[16] if len(row) > 16 else 0
            after_rewards = row[25] if len(row) > 25 else 0
            volunteer_hours = row[28] if len(row) > 28 else 0
            max_assessment = row[30] if len(row) > 30 else None
            previous_assessment = row[31] if len(row) > 31 else None
            current_assessment = row[32] if len(row) > 32 else None
            change = row[33] if len(row) > 33 else None
            cumulative_fails = row[34] if len(row) > 34 else 0
            comment = row[35] if len(row) > 35 else None

            # 找學生
            student = db.query(Student).filter(
                Student.class_id == class_id,
                Student.class_number == class_number,
            ).first()

            if not student:
                continue

            # 檢查是否已有記錄
            existing = db.query(ConductAssessment).filter(
                ConductAssessment.student_id == student.id,
                ConductAssessment.semester_id == semester_id,
            ).first()

            ca_data = {
                "student_id": student.id,
                "semester_id": semester_id,
                "fail_homework": 欠作業 or 0,
                "fail_textbook": 欠課本 or 0,
                "fail_classroom": 上課違規 or 0,
                "fail_uniform": 儀表不符 or 0,
                "fail_late": 遲到 or 0,
                "fail_absent": 缺席 or 0,
                "leave_hours": 請假 or 0,
                "before_rewards": before_rewards or 0,
                "after_rewards": after_rewards or 0,
                "volunteer_hours": float(volunteer_hours or 0),
                "max_assessment": max_assessment,
                "previous_assessment": previous_assessment,
                "current_assessment": current_assessment,
                "change": change,
                "cumulative_fails": cumulative_fails or 0,
                "comment": comment,
            }

            if existing:
                for key, value in ca_data.items():
                    setattr(existing, key, value)
            else:
                existing = ConductAssessment(**ca_data, created_by=current_user.id)
                db.add(existing)

            imported += 1

        db.commit()
        return {"message": f"成功匯入 {imported} 筆記錄"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))