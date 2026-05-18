"""
種子資料腳本 - 建立測試用學校、班級、科目、教師、學生資料
"""

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.school import School, Campus, AcademicYear, Semester
from app.models.user import User
from app.models.student import Class, Student
from app.models.subject import Subject, ClassSubject
from app.auth.jwt import hash_password


def seed():
    db = SessionLocal()
    try:
        # School
        school = School(name="測試中學", code="TEST_SCH")
        db.add(school)
        db.flush()

        # Campus
        campus = Campus(school_id=school.id, name="本校區")
        db.add(campus)
        db.flush()

        # Academic Year
        ay = AcademicYear(school_id=school.id, label="114學年度", is_current=True)
        db.add(ay)
        db.flush()

        # Semester
        sem1 = Semester(academic_year_id=ay.id, semester=1, is_current=True)
        sem2 = Semester(academic_year_id=ay.id, semester=2, is_current=False)
        db.add_all([sem1, sem2])
        db.flush()

        # Admin
        admin = User(
            school_id=school.id, username="admin", password_hash=hash_password("123456"),
            name="系統管理員", role="admin",
        )
        db.add(admin)

        # Dept Head
        dept_head = User(
            school_id=school.id, username="dept_head", password_hash=hash_password("123456"),
            name="教務主任", role="dept_head",
        )
        db.add(dept_head)
        db.flush()

        # Teachers
        teachers = []
        teacher_names = ["國文老師", "數學老師", "英文老師", "理化老師", "社會老師"]
        for i, name in enumerate(teacher_names):
            t = User(
                school_id=school.id, username=f"teacher{i+1}", password_hash=hash_password("123456"),
                name=name, role="teacher",
            )
            db.add(t)
            teachers.append(t)
        db.flush()

        # Subjects
        subject_names = [("國文", "CH"), ("數學", "MA"), ("英文", "EN"), ("理化", "PH"), ("社會", "SO")]
        subjects = []
        for name, code in subject_names:
            s = Subject(school_id=school.id, name=name, code=code)
            db.add(s)
            subjects.append(s)
        db.flush()

        # Classes (3 grades, 4 classes each)
        classes = []
        for grade in range(1, 4):
            for cls_num in range(1, 5):
                c = Class(
                    school_id=school.id, campus_id=campus.id, academic_year_id=ay.id,
                    name=f"{grade}年{cls_num}班", grade_level=grade, class_number=cls_num,
                    homeroom_teacher_id=teachers[grade - 1].id if grade <= len(teachers) else None,
                )
                db.add(c)
                classes.append(c)
        db.flush()

        # Students (30 per class)
        for c in classes:
            for s_num in range(1, 31):
                grade = c.grade_level
                cls = c.class_number
                student_no = f"{grade}{cls:02d}{s_num:02d}"
                s = Student(
                    student_no=student_no,
                    name=f"學生{grade}{cls:02d}{s_num:02d}",
                    class_id=c.id,
                )
                db.add(s)
        db.flush()

        # ClassSubjects (all subjects for all classes, semester 1)
        for c in classes:
            for i, subj in enumerate(subjects):
                cs = ClassSubject(
                    class_id=c.id, subject_id=subj.id,
                    teacher_id=teachers[i].id if i < len(teachers) else teachers[0].id,
                    semester_id=sem1.id,
                )
                db.add(cs)

        db.commit()
        print("✅ 種子資料建立完成")
        print(f"   學校: {school.name}")
        print(f"   班級: {len(classes)} 個")
        print(f"   科目: {len(subjects)} 個")
        print(f"   教師: {len(teachers) + 2} 個 (含管理員)")
        print(f"   學生: {len(classes) * 30} 個")

    except Exception as e:
        db.rollback()
        print(f"❌ 種子資料建立失敗: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()