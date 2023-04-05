from flask import Flask, request, jsonify
from conn import connection
from settings import logger
import psycopg2

app = Flask(__name__)

# Question
# Student grading system - Design a class to manage student grades,
# including entering grades, calculating averages, and generating reports.

# Query
# CREATE TABLE school(sno SERIAL PRIMARY KEY ,std_name VARCHAR(200) NOT NULL,
# grades INTEGER, average NUMERIC, report_progress VARCHAR(300));

# Table
#  sno | std_name | total | average | report_progress  | grades
# -----+----------+-------+---------+------------------+--------
#    1 | Rajguru  |   200 |    78.2 | done calculating | A
#    2 | SPB      |   250 |      76 | reviewed         | A
#    3 | arijit   |   220 |      71 | evaluating       | A
#    4 | shreya   |   210 |      70 | reviewing        | A
#    6 | Hinata   |   250 |      75 | done             | A



def handle_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except psycopg2.Error as error:
            conn = kwargs.get('conn')
            if conn:
                conn.rollback()
            logger(__name__).error(f"Error occurred: {error}")
            return jsonify({"message": f"Error occurred: {error}"})
        except Exception as error:
            logger(__name__).error(f"Error occurred: {error}")
            return jsonify({"message": f"Error occurred: {error}"})
        finally:
            conn = kwargs.get("conn")
            cur = kwargs.get("cur")
            # close the database connection
            if conn:
                conn.close()
            if cur:
                cur.close()
            logger(__name__).warning("Closing the connection")
    return wrapper


@app.route("/students", methods=["POST"])  # CREATE an item
@handle_exceptions
def add_student():
    cur, conn = connection()
    logger(__name__).warning("Starting the db connection to add new students")

    std_name = request.json["stdName"]  # string
    grades = request.json["grades"]  # int
    average = request.json["avg"]  # float
    report_progress = request.json["prog"]  # string

    # format = {
    #     "stdName": "Hinata",
    #     "grades": 700,
    #     "avg": 75,
    #     "prog": "done"
    # }

    add_query = """INSERT INTO school(std_name, grades, 
                                average, report_progress) VALUES (%s, %s, %s, %s)"""

    values = (std_name, grades, average, report_progress)
    cur.execute(add_query, values)
    conn.commit()

    logger(__name__).info(f"{std_name} added in the list")

    # close the database connection
    conn.close()
    cur.close()
    logger(__name__).warning("Hence student added, closing the connection")
    return jsonify({"message": f"{std_name} added in the list"}), 200


@app.route("/", methods=["GET"], endpoint='show_std_list')  # READ the cart list
@handle_exceptions
def show_std_list():
    cur, conn = connection()
    logger(__name__).warning("Starting the db connection to display student in the list")

    show_query = "SELECT * FROM school;"
    cur.execute(show_query)
    data = cur.fetchall()
    # Log the details into logger file
    logger(__name__).info("Displayed list of all students in the list")

    # close the database connection
    conn.close()
    cur.close()
    logger(__name__).warning("Hence students displayed, closing the connection")

    return jsonify({"message": data}), 200


@app.route("/grades/<int:sno>", methods=["PUT"], endpoint='add_grades')
@handle_exceptions
def add_grades(sno):         # updating the grades with average
    cur, conn = connection()
    logger(__name__).warning("Starting the db connection to update the details ")
    cur.execute("SELECT std_name from school where sno = %s", (sno,))
    get_std = cur.fetchone()

    if not get_std:
        return jsonify({"message": "Student not found"}), 200

    cur.execute("SELECT average FROM school WHERE sno = %s", (sno,))
    get_average = cur.fetchone()
    average = get_average[0]

    if 80 <= average or average <= 100:
        grades = "A"
    elif 65 <= average or average <= 79:
        grades = "B"
    elif 55 <= average or average <= 64:
        grades = "C"
    elif 50 <= average or average <= 54:
        grades = "D"
    else:
        grades = "E"

    query = "UPDATE school SET grades = %s WHERE sno = %s"
    values = (grades, sno)

    cur.execute(query, values)
    conn.commit()

    # Log the details into logger file
    logger(__name__).info(f"Grades of {get_std[0]} updated")

    # close the database connection
    conn.close()
    cur.close()
    logger(__name__).warning("Hence grade of student updated, closing the connection")
    return jsonify({"message": f"Grades of {get_std[0]} updated"}), 200


@app.route("/students/<int:sno>", methods=["PUT"], endpoint='update_std_details')
@handle_exceptions
def update_std_details(sno):
    cur, conn = connection()
    logger(__name__).warning("Starting the db connection to update the details ")

    cur.execute("SELECT std_name from school where sno = %s", (sno,))
    get_std = cur.fetchone()

    if not get_std:
        return jsonify({"message": "Student not found"}), 200
    data = request.get_json()
    std_name = data.get('std_name')
    grades = data.get('grades')
    average = data.get('average')
    report_progress = data.get('report_progress')

    if std_name:
        cur.execute("UPDATE school SET std_name = %s WHERE sno = %s", (std_name, sno))
    elif grades:
        cur.execute("UPDATE school SET grades = %s WHERE sno = %s", (grades, sno))
    elif average:
        cur.execute("UPDATE school SET average = %s WHERE sno = %s", (average, sno))
    elif report_progress:
        cur.execute("UPDATE school SET report_progress = %s WHERE sno = %s", (report_progress, sno))

    conn.commit()
    # Log the details into logger file
    logger(__name__).info(f"Member details updated: {data}")

    # close the database connection
    conn.close()
    cur.close()
    logger(__name__).warning("Hence student details updated, closing the connection")
    return jsonify({"message": "Student details updated", "Details": data}), 200


@app.route("/report/<int:sno>", methods=["GET"], endpoint='generate_report_card')
@handle_exceptions
def generate_report_card(sno):
    cur, conn = connection()
    logger(__name__).warning("Starting the db connection to display student report card")

    show_query = "SELECT * FROM school WHERE sno = %s;"
    cur.execute(show_query, (sno,))
    data = cur.fetchone()

    # Log the details into logger file
    logger(__name__).info(f"Displayed report card of student mo. {sno}")
    # close the database connection
    conn.close()
    cur.close()
    logger(__name__).warning("Hence students report card displayed, closing the connection")

    return jsonify({"message": data}), 200


@app.route("/delete/<int:sno>", methods=["DELETE"], endpoint='delete_student')      # DELETE an item from cart
@handle_exceptions
def delete_student(sno):
    # start the database connection
    cur, conn = connection()
    logger(__name__).warning("Starting the db connection to delete student from the list")

    delete_query = "DELETE from school WHERE sno = %s"
    cur.execute(delete_query, (sno,))

    conn.commit()
    # Log the details into logger file
    logger(__name__).info(f"student with id no. {sno} deleted from the table")

    # close the database connection
    conn.close()
    cur.close()
    logger(__name__).warning("Hence student deleted, closing the connection")

    return jsonify({"message": "Deleted Successfully", "item_no": sno}), 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)
