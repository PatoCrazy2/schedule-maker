from sqlmodel import SQLModel, Session, select, create_engine
from app.models.db_models import SourceFile, Course, TimeSlot
from app.models.schemas import DayEnum
from datetime import time, datetime
from app.utils.hashing import compute_file_hash

# Use SQLite for testing
engine = create_engine("sqlite:///testing_dedup.db")

def verify_deduplication():
    SQLModel.metadata.create_all(engine)
    
    fake_pdf_content = b"PDF_CONTENT_SIMULATION"
    file_hash = compute_file_hash(fake_pdf_content)
    filename = "test_doc.pdf"
    
    print(f"Testing with hash: {file_hash}")
    
    with Session(engine) as session:
        # 1. Simulate First Upload (Cache Miss)
        print("--- Step 1: Simulate Save (Cache Miss) ---")
        source = SourceFile(filename=filename, file_hash=file_hash)
        session.add(source)
        session.commit()
        session.refresh(source)
        
        course = Course(
            nrc="99999",
            course_code="TEST 101",
            group_code="001",
            subject_name="Testing Deduplication",
            professor="Test Bot",
            credits=5,
            source_file_id=source.id
        )
        session.add(course)
        
        slot = TimeSlot(
            day=DayEnum.FRIDAY,
            start_time=time(14, 0),
            end_time=time(16, 0),
            classroom="LAB-1"
        )
        course.time_slots.append(slot)
        session.add(course)
        session.commit()
        print("Saved SourceFile and Course to DB.")

    with Session(engine) as session:
        # 2. Simulate Second Upload (Cache Hit)
        print("\n--- Step 2: Simulate Check (Cache Hit) ---")
        existing = session.exec(select(SourceFile).where(SourceFile.file_hash == file_hash)).first()
        
        if existing:
            print("[CACHE HIT] File found in DB.")
            courses = existing.courses
            print(f"Found {len(courses)} courses.")
            for c in courses:
                print(f"Course: {c.subject_name} ({c.course_code})")
                for s in c.time_slots:
                    print(f"  Slot: {s.day} {s.start_time}-{s.end_time}")
            
            # Verify data
            assert len(courses) == 1
            assert courses[0].nrc == "99999"
            assert len(courses[0].time_slots) == 1
            print("\nVerification Successful!")
        else:
            print("❌ Verification Failed: File not found in DB.")

if __name__ == "__main__":
    verify_deduplication()
