"""cli_shirudo.py

copy of functions from anvil app for testing and development

"""

from datetime import datetime
from datetime import timedelta


def focus_from_date(date_to_use=False, style_to_use=False):
    """Returns the class focus based on a calendar lookup"""

    REF_DATE = datetime.strptime("30/06/2025", "%d/%m/%Y")

    focus_skills = {
        "SD": "Self Defence & Throws",
        "SB": "Strikes & Blocks",
        "KS": "Kicks & Sweeps",
        "SK": "Kata & Sparring",
    }
    focus_index = ["SD", "SB", "KS", "SK"]

    skill_lookup = 1
    if not date_to_use:
        date_to_use = datetime.now()

    days_since = (date_to_use - REF_DATE).days
    week_num = int((days_since / 7) % 4 + 1)
    weekday = date_to_use.strftime("%a")

    if week_num > 1:
        this_list = focus_index[-week_num + 1 :] + focus_index[: -week_num + 1 :]
    else:
        this_list = focus_index

    if weekday == "Mon":
        focus_text = focus_skills[this_list[0]]
    elif weekday == "Tue":
        focus_text = focus_skills[this_list[1]]
    elif weekday == "Wed":
        focus_text = focus_skills[this_list[2]]
    elif weekday == "Thu":
        focus_text = focus_skills[this_list[3]]
    else:
        focus_text = "Review and grading preparation"

    print(f"{days_since=}, {week_num=}, {weekday=}, {this_list=}, {focus_text=}")
    return focus_text


def run_tests():
    """Functions to run if launched locally"""

    print(f"Run from {__file__} ")
    class_focus = focus_from_date(date_to_use=datetime(2025, 7, 24))
    print(f"{class_focus=}")


if __name__ == "__main__":
    run_tests()
