import time
import csv
import requests
from operator import itemgetter
from pathlib import Path

import requests.auth
from config import settings
from jmt_utils import write_dict_to_file
from jmt_utils import write_list_to_file
from jmt_utils import d_print


def get_menu_option(menu_data=False):
    """Displays a text menu and waits for user input"""

    option_codes = list()  # list of options code, could be 1,2,3 or "a,b,x" etc

    if not menu_data:
        menu_list = list()
        menu_list.append(
            {
                "shortcut": "s",
                "description": "Sleep for a time you'll add a number for in seconds",
            }
        )
        menu_list.append({"shortcut": "x", "description": "Exit"})

    # Build the menu
    for menu_detail in menu_list:
        this_option = menu_detail["shortcut"]
        this_desc = menu_detail["description"]
        assert this_option not in option_codes, f"Duplicate option: {this_option}"
        option_codes.append(this_option)

    pad_length = 2

    menu_prompt = "Choose an option:"

    while True:
        print(f"{menu_prompt}")
        count_options = 0
        for menu_detail in menu_list:
            print(f"{menu_detail['shortcut']} {menu_detail['description']}")
            count_options += 1
        print()
        user_text = input("Option: ")

        clean_input = user_text.strip()
        if clean_input in option_codes:
            return clean_input
        else:
            print("\nInvalid selection, please try again\n")


def menu_generator(menu_type=False):
    """Generates a menu based on the supplied type"""

    menu_list = list()
    # menu_options = list()
    # menu_descriptions = list()

    if not menu_type:
        menu_detail = dict()
        menu_detail["shortcut"] = "t"
        menu_detail["description"] = "Show the time and date"
        menu_list.append(menu_detail)
        menu_detail = dict()
        menu_detail["shortcut"] = "q"
        menu_detail["description"] = "Quit"
        menu_list.append(menu_detail)
        return menu_list

    if menu_type == "grading_data":

        menu_detail = dict()
        menu_detail["shortcut"] = "r"
        menu_detail["description"] = "Parse Clubworx grading report"
        menu_list.append(menu_detail)
        menu_detail = dict()
        menu_detail["shortcut"] = "q"
        menu_detail["description"] = "Quit"
        menu_list.append(menu_detail)

        return menu_list

    return False


def start_menu():
    """Present the user with a menu"""

    print("Program started")
    keep_running = True

    menu_data = menu_generator("grading_data")
    assert menu_data, "No valid menu type specified"

    while keep_running:
        user_selection = get_menu_option(menu_data)
        if user_selection == "x":
            keep_running = False

    print("All done")


def grading_list_one_off():
    """Reads the grading sreport from clubworx

    This is the list of students for a grading event
    used to prepare the grading attendance sheet

    """
    # input_folder = "/home/john/SynologyDrive/Shirudo/Gradings/2024"
    input_folder = Path(settings["input_folder"]) / "Gradings"
    input_filename = "Grading_export_2024-03-02.md"

    file_name = Path(input_folder) / input_filename

    student_details = dict()
    all_students = list()

    with open(file_name, "r") as input_file:
        read_state = 0
        line_data = list()
        line_count = 0
        detail_count = 0
        for each_line in input_file:
            clean_line = each_line.strip()
            if clean_line:
                if read_state == 0:  # Not processing a user yet
                    read_state = 1
                    detail_count = 0
                    student_details = dict()
                elif read_state == 1:  # Looking for name
                    if detail_count == 1:
                        student_details["name"] = clean_line
                    elif detail_count == 2:
                        size_text = int(clean_line[clean_line.rfind(" ") :])
                        student_details["belt size"] = int(size_text)
                    elif detail_count == 5:
                        belt_parts = clean_line.split("Belt /")
                        assert len(belt_parts) == 2, "Unexpected split in {clean_line}"
                        belt_current = belt_parts[0].strip()
                        belt_new = belt_parts[1].strip()[:-5]
                        student_details["rank-now"] = belt_current
                        student_details["rank-post"] = belt_new
                    elif detail_count == 6:
                        pos_left = clean_line.rfind("(") + 1
                        pos_right = clean_line.find(" ", pos_left)
                        classes_since = int(clean_line[pos_left:pos_right])
                        student_details["classes"] = classes_since
                line_count += 1
                detail_count += 1
            else:
                if read_state == 1:  # Blank after reading data
                    all_students.append(student_details)
                    print(f"Have data: {student_details}")
                    read_state = 0

    output_folder = Path(settings["output_folder"])
    output_filename = "Grading_prep_summary.csv"

    file_name = Path(output_folder) / output_filename
    write_list_to_file(all_students, file_name)


def process_raw_attendance_file():
    """reads the raw text file and compiled student stats"""

    count_lines = 0
    student_data = dict()
    day_data = dict()

    input_folder = (
        Path(settings["input_folder"]) / "Attendance" / "Raw_class_attendance"
    )
    input_filename = "Shirudo_attendance_2024-01-31.txt"

    filename = input_folder / input_filename

    current_student = False
    current_day = "Empty"
    last_line = ""

    with open(filename, "r") as input_file:
        for each_line in input_file.readlines():
            clean_line = each_line.strip()
            count_lines += 1
            if clean_line == "Attended":
                assert (
                    current_student
                ), f"Line: {count_lines:03} Non attending {clean_line}"
                d_print("    Have attended finish", 10)
                if current_student in student_data:
                    student_detail = student_data[current_student]
                else:
                    student_detail = dict()
                    student_detail["name"] = current_student
                    student_detail["class_count"] = 0
                student_detail["class_count"] += 1
                # data_for_day = day_data[current_day]
                day_data[current_day] += 1
                student_data[current_student] = student_detail
                current_student = False
                d_print(f"    Added student: {student_detail}", 10)

            elif clean_line == "":
                if current_student:
                    if last_line in ("Booked", "Booked"):
                        current_student = False  # Discard current entry
                        pass
                    else:
                        assert (
                            current_student == ""
                        ), f"Line: {count_lines:03} Non attending [{current_student}]"
                else:
                    pass
                    d_print(f"    Skipping blank line at {count_lines}", 10)
            elif "@" in clean_line:
                assert current_student, f"Email before student at line {count_lines}"
                d_print(f"Email address at line {count_lines} : {clean_line}", 20)
            elif clean_line.startswith("Class, "):
                class_parts = clean_line.split(",")
                clean_parts = [each_part.strip() for each_part in class_parts]
                d_print(f"Class data: {clean_parts}", 30)
                # this_day = clean_parts[2]
                this_day = f"{clean_parts[2]} {clean_parts[4]}"
                if this_day not in day_data:
                    day_data[this_day] = 0
                current_day = this_day

            else:
                current_student = clean_line
                d_print(f"\n --> Set current student to: {current_student}", 20)
            last_line = clean_line

    d_print(f"Processed {count_lines} lines in {input_filename}", 1000)
    d_print(day_data, 50)
    d_print(student_data, 0)

    return (student_data, day_data)


def save_class_attendance_to_file(student_data, day_data):
    """Save the supplied student attendance data to a csv file"""

    output_folder = Path(settings["output_folder"])
    filename = output_folder / "Attendance_output.csv"

    with open(filename, "w") as output_file:
        for student_key, student_detail in sorted(student_data.items()):
            this_line = f'{student_detail["name"]},{student_detail["class_count"]}\n'
            d_print(this_line.strip(), 20)
            output_file.write(this_line)

    output_folder = Path(settings["output_folder"])
    filename = output_folder / "Attendance_day_summary.csv"

    sorted_day_keys = list(day_data.keys())
    sorted_day_keys.sort()

    sorted_days = {i: day_data[i] for i in sorted_day_keys}

    write_dict_to_file((sorted_days), filename)

    return filename


def attendance_one_off():
    """Processes a compilation of all attendances for a month (or range)

    Files created by copying and pasting from each class into file
    which also includes the class instructor and time info
    """

    student_data, day_data = process_raw_attendance_file()
    saved_file = save_class_attendance_to_file(student_data, day_data)

    print(f"Created file: {saved_file}")


def clean_attendance_export_file(
    csv_file_name_without_extension,
    valid_styles=["Shirudo Hybrid", "SHIRUDO Little Ninja's"],
):
    """Imports an attendacnce output file and removes entries with 0 attendance. File looks like:

    Contact ID,First Name,Last Name,Member Number,Age,Attendances (Last 30 days)
    123456,John,Doe,,,3

    Contact ID,First Name,Last Name,Member Number,Age,Attendances (Last 30 days),Current Rank,Style,Date of Birth

    """

    full_path = Path(settings.INPUT_FOLDER) / f"{csv_file_name_without_extension}.csv"
    print(f"Input file for clean import is :\n{full_path}")

    student_list = list()
    student_dict = {}
    id_list = list()
    count_zeroes = 0
    count_other_styles = 0
    data_headers = list()
    row_count = 0

    with open(full_path, "r") as input_file:
        csv_reader = csv.reader(input_file)
        for each_row in csv_reader:
            row_count += 1
            if row_count == 1:
                data_headers = each_row
                assert data_headers[0] == "Contact ID", f"Invalid: [{data_headers[0]}]"
                assert data_headers[5].startswith("Attendances"), "Invalid data headers"
            else:
                student_attendances = int(each_row[5])
                if student_attendances:
                    student_id = each_row[0]

                    student_name = f"{each_row[1]} {each_row[2]}"
                    student_rank = each_row[6].strip()
                    student_style = each_row[7].strip()
                    student_dob = each_row[8].strip()
                    if student_style in valid_styles:
                        assert student_id not in id_list, f"Duplicate ID: {student_id}"
                        id_list.append(student_id)
                        this_student = {
                            "ID": student_id,
                            "name": student_name,
                            "attendances": student_attendances,
                            "style": student_style,
                            "rank": student_rank,
                            "dob": student_dob,
                        }
                        student_list.append(this_student)
                        student_dict["student_id"] = this_student
                    else:
                        count_other_styles += 1
                        print(
                            f"Skipping student {count_other_styles:02} from style:'{student_style}' , {student_name} , {student_attendances} attendances"
                        )

                else:
                    count_zeroes += 1

    print(
        f"Finished with {len(student_list)} students from styles:{valid_styles}, skipping({count_zeroes} with zero attendance and {count_other_styles} from other styles)"
    )

    full_path = (
        Path(settings.OUTPUT_FOLDER) / f"{csv_file_name_without_extension}_filtered.csv"
    )
    sorted_list = sorted(student_list, key=itemgetter("attendances"), reverse=True)

    print(f"Output file is:\n{full_path}")
    write_list_to_file(sorted_list, full_path)

    return student_dict


def read_student_data(student_data_file_without_extention):
    """Reads the master student data - our compiled data"""

    full_path = (
        Path(settings.INPUT_FOLDER) / f"{student_data_file_without_extention}.csv"
    )
    print(f"Input student file is:\n{full_path}")

    student_dict = dict()
    id_list = list()
    count_zeroes = 0
    header_index = dict()
    row_count = 0

    with open(full_path, "r") as input_file:
        csv_reader = csv.reader(input_file)
        for each_row in csv_reader:
            row_count += 1
            if row_count == 1:
                col_num = 0
                for each_header in each_row:
                    header_index[each_header.strip()] = col_num
                    col_num += 1
                assert "Number" in header_index, "Invalid data headers"
                assert "Name" in header_index, "Invalid data headers"
            else:
                # Name                 ,Type ,Number  ,Family  ,Activated  ,DOB        ,Last Grading
                student = dict()
                student_ID = each_row[header_index["Number"]].strip()
                assert student_ID not in student_dict, f"Duplicate ID: {student_ID}"
                student["Name"] = each_row[header_index["Name"]].strip()
                student["Family"] = each_row[header_index["Family"]].strip()

                student_dict[student_ID] = student
                # print(f"Student: [{student_ID}] -read as [{student["Name"]}]")

    return student_dict


def read_attendance_file(csv_file_name_without_extention):
    """Imports an already processed attendance file. File looks like:

    1455548,Some Name,11
    """

    full_path = Path(settings.INPUT_FOLDER) / f"{csv_file_name_without_extention}.csv"
    print(f"Input file is:\n{full_path}")

    student_list = dict()
    id_list = list()

    with open(full_path, "r") as input_file:
        csv_reader = csv.reader(input_file)
        for each_row in csv_reader:
            student_id = each_row[0].strip()
            student_name = each_row[1].strip()
            student_attendances = int(each_row[2])
            assert student_id not in id_list, f"Duplicate ID: {student_id}"
            id_list.append(student_id)
            student_list[student_id] = {
                "Name": student_name,
                "Attendances": student_attendances,
            }
            # print(f"[{student_id}] is [{student_list[student_id]}]")

    return student_list


def do_one_off():
    """Meant to be temporary code to be pulled in to main functions"""
    # grading_list_one_off()
    # attendance_one_off()

    input_file_name = settings.MEMBER_DATA_CSV
    student_data = read_student_data(input_file_name)
    print(f"Read {len(student_data)} entries from student database csv file")

    input_file_name = settings.REPORT_365_day
    attendance_data = clean_attendance_export_file(input_file_name)
    print(
        f"Read attendance data for {len(attendance_data)} students from: {input_file_name}"
    )

    for att_id, att_data in attendance_data.items():
        if att_id in student_data:
            style_curr = student_data.get("Style", False)
            style_attn = att_data.get("Style", False)
            if style_attn:
                if style_curr:
                    assert style_curr == style_attn, f"Style mismatch for ID {att_id}"
                else:
                    print(f"Missing style info for ID {att_id}")
            else:
                print(f"No style info for student ID {att_id} - {att_data['name']}")

        else:
            print(f"Missing data for student: [{att_id}] - [{att_data['name']}]")


def add_rank_column():
    """Reads a csv file, calculating a rank and adding an extra column"""

    input_file_name = (
        Path(settings.INPUT_FOLDER) / f"{settings.REPORT_365_day}_filtered.csv"
    )
    output_file_name = (
        Path(settings.INPUT_FOLDER) / f"{settings.REPORT_365_day}_combined_ranked.csv"
    )

    user_data = dict()

    with open(input_file_name, "r") as input_file:

        count_input = 0
        for each_line in input_file.readlines():
            output_line = list()
            raw_parts = each_line.split(",")
            for each_part in raw_parts:
                clean_part = each_part.strip()
                output_line.append(each_part)
            grading_part = raw_parts[5]
            if "kyu" in grading_part.lower():
                grade = int(grading_part[0:1])
            elif "provisional black" in grading_part.lower():
                grade = 0
            elif "dan" in grading_part.lower():
                grade = int(grading_part[0:1]) * -1
            else:
                assert False, f"Unhandled: {grading_part} from {each_line}"
                print("Unhandled")
            output_line.append(grade)
            print(f"{output_line} - {grading_part}")
            user_id = raw_parts[0].strip()
            user_dict = dict()
            user_dict["name"] = raw_parts[1].strip()
            user_dict["classes_365"] = raw_parts[2].strip()
            user_dict["style"] = raw_parts[3].strip()
            user_dict["dob"] = raw_parts[4].strip()
            user_dict["text_rank"] = raw_parts[5].strip()
            user_dict["sort_rank"] = grade
            user_dict["classes_30"] = 0
            user_data[user_id] = user_dict

    input_file_name = (
        Path(settings.INPUT_FOLDER) / f"{settings.REPORT_30_day}_filtered.csv"
    )
    with open(input_file_name, "r") as input_file:

        count_input = 0
        for each_line in input_file.readlines():
            output_line = list()
            raw_parts = each_line.split(",")
            user_id = raw_parts[0].strip()
            user_classes = int(raw_parts[2].strip())
            assert user_id in user_data.keys(), f"Missing user: {user_id}"
            user_data[user_id]["classes_30"] = user_classes

    formatted_list = list()
    formatted_list.append(
        [
            "id",
            "name",
            "style",
            "dob",
            "text-rank",
            "sort-rank",
            "classes_365",
            "classes_30",
        ]
    )

    for user_id, user_detail in user_data.items():
        this_line = list()
        this_line.append(user_id)
        this_line.append(user_detail["name"])
        this_line.append(user_detail["style"])
        this_line.append(user_detail["dob"])
        this_line.append(user_detail["text_rank"])
        this_line.append(user_detail["sort_rank"])
        this_line.append(user_detail["classes_365"])
        this_line.append(user_detail["classes_30"])
        formatted_list.append(this_line)

    output_ok = write_list_to_file(formatted_list, output_file_name)


def get_clubworx_user_data(user_id=False):
    """Reads student data from the clubworx web page"""

    member_url = settings.CLUBWORX_URL_MEMBER.replace("MEMBER_ID", user_id)
    req_auth = requests.auth.HTTPBasicAuth(
        settings.CLUBWORX_USER, settings.CLUBWORX_CRED
    )

    req_response = requests.get(member_url, auth=req_auth)
    req_text = req_response.text
    print(req_response)
    print(req_text)

    print("All done")


if __name__ == "__main__":
    # start_menu()
    # do_one_off()
    add_rank_column()
    # get_clubworx_user_data("1950710")
