"""種子資料腳本 — 建立測試用學校、班級、學生、科目、使用者"""

from app.database import engine, SessionLocal, Base
from app.models.school import School, Campus, AcademicYear, Semester
from app.models.user import User
from app.models.student import Class, Student
from app.models.subject import Subject, ClassSubject
from app.auth.jwt import hash_password
from sqlalchemy import text


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 檢查是否已有資料
        if db.query(School).first():
            print("資料庫已有資料，跳過種子")
            return

        # === 學校 ===
        school = School(name="明德國中", code="MDJH")
        db.add(school)
        db.flush()

        campus = Campus(school_id=school.id, name="本部校區")
        db.add(campus)
        db.flush()

        ay = AcademicYear(school_id=school.id, label="114學年度", is_current=True)
        db.add(ay)
        db.flush()

        s1 = Semester(academic_year_id=ay.id, semester=1, is_current=True)
        s2 = Semester(academic_year_id=ay.id, semester=2, is_current=False)
        db.add_all([s1, s2])
        db.flush()

        # === 使用者 ===
        users_data = [
            ("admin", "系統管理員", "admin"),
            ("dept_head", "教務主任", "dept_head"),
            ("teacher_wang", "王老師", "teacher"),
            ("teacher_lee", "李老師", "teacher"),
            ("teacher_chen", "陳老師", "teacher"),
            ("teacher_lin", "林老師", "teacher"),
            ("teacher_huang", "黃老師", "teacher"),
        ]
        user_objs = []
        for username, name, role in users_data:
            u = User(
                school_id=school.id,
                username=username,
                password_hash=hash_password("123456"),
                name=name,
                role=role,
            )
            db.add(u)
            user_objs.append(u)
        db.flush()

        # === 科目 ===
        subjects_data = [
            ("國文", "CHI"), ("數學", "MAT"), ("英文", "ENG"),
            ("自然", "SCI"), ("社會", "SOC"),
        ]
        subject_objs = []
        for name, code in subjects_data:
            s = Subject(school_id=school.id, name=name, code=code)
            db.add(s)
            subject_objs.append(s)
        db.flush()

        # === 班級（一年級1~4班，二年級1~4班，三年級1~4班）===
        class_objs = []
        for grade in range(1, 4):
            for cls_num in range(1, 5):
                c = Class(
                    school_id=school.id,
                    campus_id=campus.id,
                    academic_year_id=ay.id,
                    name=f"{grade}年{cls_num}班",
                    grade_level=grade,
                    class_number=cls_num,
                    homeroom_teacher_id=user_objs[grade * 2 - 1].id,
                )
                db.add(c)
                class_objs.append(c)
        db.flush()

        # === 學生（每班30人）===
        last_names = "王李張劉陳楊趙黃周吳徐孫胡朱高林何郭馬羅"
        first_names_m = "志明建國文雄偉杰俊豪強龍"
        first_names_f = "淑芬美玲雅芳麗華秀英慧敏靜宜"

        student_count = 0
        for cls in class_objs:
            for i in range(1, 31):
                import random
                ln = last_names[random.randint(0, len(last_names) - 1)]
                fn_pool = first_names_m if i % 2 == 0 else first_names_f
                fn = fn_pool[random.randint(0, len(fn_pool) - 1)]
                student_count += 1
                stu = Student(
                    student_no=f"{cls.grade_level}{cls.class_number:02d}{i:02d}",
                    name=ln + fn,
                    class_id=cls.id,
                    status="active",
                )
                db.add(stu)
        db.flush()

        # === 班級科目（每班5科，分配老師）===
        for cls in class_objs:
            for idx, sub in enumerate(subject_objs):
                teacher_idx = (idx + 2) % len(user_objs)  # 輪流分配
                cs = ClassSubject(
                    class_id=cls.id,
                    subject_id=sub.id,
                    teacher_id=user_objs[teacher_idx].id,
                    semester_id=s1.id,
                )
                db.add(cs)
        db.flush()

        db.commit()
        print(f"種子資料建立完成：1學校, {len(class_objs)}班級, {len(subject_objs)}科目, {len(user_objs)}使用者, {student_count}學生")

    except Exception as e:
        db.rollback()
        print(f"種子資料錯誤：{e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
