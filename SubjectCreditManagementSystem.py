import sqlite3
import itertools
def initialize_db():
    conn = sqlite3.connect("college.db")
    cursor = conn.cursor()

    cursor.executescript('''
    CREATE TABLE IF NOT EXISTS Users (
        Username TEXT PRIMARY KEY,
        Password TEXT NOT NULL,
        Role TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS Courses (
        CourseID INTEGER PRIMARY KEY,
        CourseName TEXT NOT NULL,
        Credits INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS StudentCourses (
        StudentUSN TEXT NOT NULL,
        CourseID INTEGER NOT NULL,
        PRIMARY KEY (StudentUSN, CourseID),
        FOREIGN KEY (CourseID) REFERENCES Courses(CourseID)
    );

    CREATE TABLE IF NOT EXISTS Grades (
        StudentUSN TEXT NOT NULL,
        CourseID INTEGER NOT NULL,
        Grade TEXT,
        PRIMARY KEY (StudentUSN, CourseID),
        FOREIGN KEY (CourseID) REFERENCES Courses(CourseID)
    );

    INSERT OR IGNORE INTO Users (Username, Password, Role) VALUES 
        ('student', '1234', 'student'),
        ('teacher', 'abcd', 'teacher'),
        ('principal', 'admin1', 'principal'),
        ('admin', 'root', 'admin');
    
    

    INSERT OR IGNORE INTO Courses (CourseID, CourseName, Credits) VALUES
        (1, 'Maths', 2),
        (2, 'DBMS', 4),
        (3, 'ADA', 3),
        (4, 'Biology', 1),
        (5, 'Computer Science', 1),
        (6, 'AJAVA', 1),
        (7, 'UHV', 1),
        (8, 'UI/UX', 1);
    ''')

    conn.commit()
    conn.close()


def authenticate_user(username, password):
    conn = sqlite3.connect("college.db")
    cursor = conn.cursor()
    cursor.execute("SELECT Role FROM Users WHERE Username=? AND Password=?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None



def clear_records():
    conn = sqlite3.connect("college.db")
    cursor = conn.cursor()
    cursor.executescript('''
    DELETE FROM StudentCourses;
    DELETE FROM Grades;
    ''')
    conn.commit()
    conn.close()
    print("All student enrollments and grades have been cleared.")



def knapsack_max_credits(student_usn, max_credits=7, max_courses=4):
    conn = sqlite3.connect("college.db")
    cursor = conn.cursor()

    cursor.execute("SELECT CourseID, CourseName, Credits FROM Courses")
    courses = cursor.fetchall()

    try:
        num_courses = int(input(f"How many courses do you want to select (up to {max_courses} courses)? "))
    except ValueError:
        conn.close()
        return "Invalid input. Please enter a number."

    if num_courses > max_courses or num_courses < 1:
        conn.close()
        return f"You can select a minimum of 1 and a maximum of {max_courses} courses."

    cursor.execute("SELECT CourseID FROM StudentCourses WHERE StudentUSN=?", (student_usn,))
    enrolled_ids = set(row[0] for row in cursor.fetchall())
    available_courses = [c for c in courses if c[0] not in enrolled_ids]

    valid_combos = []
    for combo in itertools.combinations(available_courses, num_courses):
        credit_sum = sum(course[2] for course in combo)
        if credit_sum <= max_credits:
            valid_combos.append((combo, credit_sum))

    if not valid_combos:
        conn.close()
        return f"No valid combination of exactly {num_courses} courses found within the credit limit of {max_credits}."

    best_combo, max_credit_sum = max(valid_combos, key=lambda x: x[1])

    for cid, _, _ in best_combo:
        cursor.execute("INSERT INTO StudentCourses (StudentUSN, CourseID) VALUES (?, ?)", (student_usn, cid))

    conn.commit()
    conn.close()

    result = f"Bot: Student {student_usn} enrolled in {len(best_combo)} course(s):\n"
    for cid, cname, _ in best_combo:
        result += f"{cid}: {cname}\n"
    result += f"Total Credits: {max_credit_sum}."
    return result



def chatbot_query(user_role):
    conn = sqlite3.connect("college.db")
    cursor = conn.cursor()

    if user_role == "student":
        student_usn = input("Enter your USN: ")
        while True:
            print("\n1. Enroll in courses\n2. View my courses\n3. Logout")
            choice = input("Choose an option: ")

            if choice == "1":
                result = knapsack_max_credits(student_usn)
            elif choice == "2":
                cursor.execute("""
                SELECT c.CourseID, c.CourseName, c.Credits FROM Courses c
                JOIN StudentCourses sc ON c.CourseID = sc.CourseID
                WHERE sc.StudentUSN = ?
                """, (student_usn,))
                courses = cursor.fetchall()
                if courses:
                    result = f"Courses enrolled by {student_usn}:\n" + "\n".join([f"{cid}: {cname} ({credits} credits)" for cid, cname, credits in courses])
                else:
                    result = "No enrolled courses found."
            elif choice == "3":
                conn.close()
                return "Logging out..."
            else:
                result = "Invalid option."
            print("\nBot:", result)

    elif user_role == "teacher":
        username = "teacher"
        while True:
            print("\n1. View list of courses\n2. Assign grade to student\n3. View student details\n4. Remove student course record\n5. Logout")
            choice = input("Choose an option: ")

            if choice == "1":
                cursor.execute("SELECT CourseID, CourseName, Credits FROM Courses")
                courses = cursor.fetchall()
                result = "Courses:\n" + "\n".join([f"{cid} - {name} ({credits} credits)" for cid, name, credits in courses])

            elif choice == "2":
                student_usn = input("Enter Student USN: ")
                course_id = input("Enter Course ID: ")

                cursor.execute("""
                    SELECT 1 FROM StudentCourses 
                    WHERE StudentUSN = ? AND CourseID = ?
                """, (student_usn, course_id))
                if cursor.fetchone():
                    grade = input("Enter Grade (A/B/C/D/F): ")
                    cursor.execute("INSERT OR REPLACE INTO Grades (StudentUSN, CourseID, Grade) VALUES (?, ?, ?)",
                                   (student_usn, course_id, grade))
                    conn.commit()
                    result = f"Grade {grade} assigned to student {student_usn} for course {course_id}."
                else:
                    result = f"Cannot assign grade. Student {student_usn} is not enrolled in course {course_id}."

            elif choice == "3":
                student_usn = input("Enter Student USN: ")
                cursor.execute("""
                SELECT c.CourseName, g.Grade FROM Grades g
                JOIN Courses c ON g.CourseID = c.CourseID
                WHERE g.StudentUSN = ?
                """, (student_usn,))
                details = cursor.fetchall()
                if details:
                    result = f"Details for student {student_usn}:\n" + "\n".join([f"{course}: {grade}" for course, grade in details])
                else:
                    result = "No data found for this student."

            elif choice == "4":
                student_usn = input("Enter Student USN to remove record: ")
                course_id = input("Enter Course ID to remove: ")
                cursor.execute("DELETE FROM StudentCourses WHERE StudentUSN = ? AND CourseID = ?", (student_usn, course_id))
                cursor.execute("DELETE FROM Grades WHERE StudentUSN = ? AND CourseID = ?", (student_usn, course_id))
                conn.commit()
                result = f"Removed enrollment and grade record for student {student_usn} in course {course_id}."

            elif choice == "5":
                conn.close()
                return "Logging out..."
            else:
                result = "Invalid option."
            print("\nBot:", result)

    elif user_role == "principal":
        username = "principal"
        while True:
            print("\n1. View all students and their courses\n2. View all grades\n3. Clear all records\n4. Logout")
            choice = input("Choose an option: ")

            if choice == "1":
                cursor.execute("""
                SELECT sc.StudentUSN, c.CourseName FROM StudentCourses sc
                JOIN Courses c ON sc.CourseID = c.CourseID
                """)
                rows = cursor.fetchall()
                if rows:
                    student_map = {}
                    for usn, course in rows:
                        student_map.setdefault(usn, []).append(course)
                    result = "Student Enrollments:\n"
                    for usn, courses in student_map.items():
                        result += f"{usn}: {', '.join(courses)}\n"
                else:
                    result = "No enrollments found."

            elif choice == "2":
                cursor.execute("""
                SELECT g.StudentUSN, c.CourseName, g.Grade FROM Grades g
                JOIN Courses c ON g.CourseID = c.CourseID
                """)
                rows = cursor.fetchall()
                if rows:
                    result = "Grades:\n" + "\n".join([f"{usn} - {course}: {grade}" for usn, course, grade in rows])
                else:
                    result = "No grades recorded."

            elif choice == "3":
                clear_records()
                result = "All records cleared."

            elif choice == "4":
                conn.close()
                return "Logging out..."
            else:
                result = "Invalid option."
            print("\nBot:", result)

    else:
        result = "No options implemented for this role yet."
        print("\nBot:", result)

    conn.close()
    return result


def chat_interface():
    while True:
        username = input("Enter username: ")
        password = input("Enter password: ")
        user_role = authenticate_user(username, password)

        if user_role:
            print(f"\nWelcome, {user_role.capitalize()}!")
            while True:
                response = chatbot_query(user_role)
                print("\nBot:", response)
                if response == "Logging out...":
                    break
        else:
            print("Invalid credentials. Please try again.")

        logout = input("\nDo you want to login with another user? (yes/no): ")
        if logout.lower() != "yes":
            print("Exiting the system. Goodbye!")
            break


if __name__== "_main_":
    initialize_db()
    chat_interface()

'''if _name_ == "_main_":
    initialize_db()
    clear_records()  # Ensures clean slate
    usn = "1BI22CS001"
    print(knapsack_max_credits(usn))'''