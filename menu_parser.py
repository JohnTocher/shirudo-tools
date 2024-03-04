import time
from pathlib import Path
from config import settings
from jmt_utils import write_dict_to_file
from jmt_utils import write_list_to_file
from jmt_utils import d_print

def get_menu_option(menu_data=False):
    """ Displays a text menu and waits for usedr input """

    option_codes = list()   # list of options code, could be 1,2,3 or "a,b,x" etc
    
    if not menu_data:
        menu_list = list()
        menu_list.append({"shortcut":"s","description":"Sleep for a time you'll add a number for in seconds"})
        menu_list.append({"shortcut":"x","description":"Exit"})

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
    """ Generates a menu based on the supplied type """

    menu_list = list()
    #menu_options = list()
    #menu_descriptions = list()

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
    """ Present the user with a menu """

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
    """ Reads the grading sreport from clubworx
    
        This is the list of students for a grading event
        used to prepare the grading attendance sheet

    """
    #input_folder = "/home/john/SynologyDrive/Shirudo/Gradings/2024"
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
                if read_state == 0: # Not processing a user yet
                    read_state = 1
                    detail_count = 0
                    student_details = dict()
                elif read_state == 1: #Looking for name
                    if detail_count == 1:
                        student_details["name"] = clean_line
                    elif detail_count == 2:
                        size_text = int(clean_line[clean_line.rfind(" "):])
                        student_details["belt size"] = int(size_text)
                    elif detail_count == 5:
                        belt_parts = clean_line.split("Belt /")
                        assert len(belt_parts) ==2, "Unexpected split in {clean_line}"
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
                if read_state == 1: # Blank after reading data
                    all_students.append(student_details)
                    print(f"Have data: {student_details}")
                    read_state = 0
        
    output_folder = Path(settings["output_folder"])
    output_filename = "Grading_prep_summary.csv"

    file_name = Path(output_folder) / output_filename
    write_list_to_file(all_students,file_name)


def process_raw_attendance_file():
    """ reads the raw text file and compiled student stats"""

    count_lines = 0
    student_data = dict()
    day_data = dict()
    
    input_folder = Path(settings["input_folder"]) / "Attendance" / "Raw_class_attendance"
    input_filename = "Shirudo_attendance_2024-01-31.txt"

    filename = input_folder / input_filename

    current_student = False
    current_day = "Empty"
    last_line = ""

    with open(filename ,"r") as input_file:
        for each_line in input_file.readlines():
            clean_line = each_line.strip()
            count_lines += 1
            if clean_line == "Attended":
                assert current_student, f"Line: {count_lines:03} Non attending {clean_line}"
                d_print("    Have attended finish", 10)
                if current_student in student_data:
                    student_detail = student_data[current_student]
                else:
                    student_detail = dict()
                    student_detail["name"] = current_student
                    student_detail["class_count"] = 0
                student_detail["class_count"] += 1
                #data_for_day = day_data[current_day]
                day_data[current_day] += 1
                student_data[current_student] = student_detail
                current_student = False
                d_print(f"    Added student: {student_detail}", 10)

            elif clean_line == "":
                if current_student:
                    if last_line in ("Booked", "Booked"):
                        current_student = False # Discard current entry 
                        pass
                    else:
                        assert current_student == "", f"Line: {count_lines:03} Non attending [{current_student}]"
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
                #this_day = clean_parts[2]
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
    """ Save the supplied student attendance data to a csv file """

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
    """ Processes a compilation of all attendaces for a month (or range)
    
        Files created by copying and pasting from each class into file
        which also includes the class instructor and time info
    """

    student_data, day_data = process_raw_attendance_file()
    saved_file = save_class_attendance_to_file(student_data, day_data)

    print(f"Created file: {saved_file}")

def do_one_off():
    """ Meant to be temporary code to be pulled in to main functions
    """
    # grading_list_one_off()
    attendance_one_off()


if __name__ == "__main__":
    # start_menu()
    do_one_off()

