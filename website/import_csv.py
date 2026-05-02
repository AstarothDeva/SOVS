from website.database import get_db_connection
import csv

conn = get_db_connection()
with open('student.csv', 'r')as file:
    reader = csv.DictReader(file)
    print(reader.fieldnames)

    for row in reader:
        try:
            print(row)
            conn.execute(
                "INSERT OR IGNORE INTO users (student_id, password, email) VALUES (?,?,?)",
            (row['student_id'], row['password'], row['email']))
        except Exception as error:
            print("Error inserting row.", error)
            print("Error: ", error)

conn.commit()
conn.close()