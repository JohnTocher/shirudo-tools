# General purpose reusable utilities by JMT
# 
# Version 1.1

GLOBAL_DEBUG_LEVEL = 50
DEBUG_COUNT_LIMIT = 5

def d_print(msg_to_print, msg_priority):
    """ Prints the supplied messgae if the provided priority
        is greater than or equal to the global constant
        GLOBAL_DEBUG_LEVEL
    """
    
    if msg_priority >= GLOBAL_DEBUG_LEVEL:
        print(msg_to_print)


def write_list_to_file(list_to_save, file_to_write, write_dict_headers=False):
    """ Takes a list of file names (really anything that can safely be converted to text) and writes it to the filename supplied
    """

    write_count = 0

    try:
        with open (file_to_write, "w") as output_file:
            for each_item in list_to_save:
                write_count += 1
                if write_count < DEBUG_COUNT_LIMIT:
                    print(f"{write_count:05} ==> {each_item}")
                if isinstance(each_item, list):
                    output_string = ""
                    for each_sub in each_item:
                        if output_string:
                            output_string = f"{output_string},{each_sub}"
                        else:
                            output_string = f"{each_sub}"
                    output_file.write(f"{output_string}\n")
                elif isinstance(each_item, dict):
                    output_string = ""
                    if (write_count == 1) and write_dict_headers:
                        for each_key in each_item.keys():
                            if output_string:
                                output_string = f"{output_string},{each_key}"
                            else:
                                output_string = f"{each_key}"
                        output_file.write(f"{output_string}\n")
                        output_string = ""
                    for each_sub in each_item.values():
                        if output_string:
                            output_string = f"{output_string},{each_sub}"
                        else:
                            output_string = f"{each_sub}"
                    output_file.write(f"{output_string}\n")
                else:
                    output_file.write(f"{str(each_item)}\n")
    except IOError:
        d_print("Error writing to file: {}", 100)
        return False
    
    return len(list_to_save)


def write_dict_to_file(dict_to_save, file_to_write):
    """ Takes a dictionary (really anything that can safely be converted to text) and writes it to the filename supplied
    """

    item_list = list()

    for dict_key, dict_val in dict_to_save.items():
        new_line = f"{dict_key}"
        #d_print(f"Values: {dict_val}", 20)
        if isinstance(dict_val, dict):   # Dictionary of dictionaries
            val_list = [this_val for this_val in dict_val.items()]
        elif isinstance(dict_val, list):
            val_list = dict_val
        elif isinstance(dict_val, str):
            val_list = dict_val.split(",")
        elif isinstance(dict_val, int):
            val_list = list()
            val_list.append(dict_val)
        else:
            val_list = list(dict_val)
        for each_val in val_list:
            new_line = f"{new_line},{each_val}"
        item_list.append(new_line)

    write_list_to_file(item_list, file_to_write)

    return f"Wrote dict to: {file_to_write}"

def remove_line_breaks_and_commas(input_text):
    """ Removes newlines, linebreaks and commas, replacing each with a space
    """

    if input_text:
        new_text = input_text.replace("\r", " ")
        new_text = new_text.replace("\n", " ")
        new_text = new_text.replace(",", " ")
    else:
        new_text = ""

    return new_text

if __name__ =="__main__":
    d_print(f"{__file__} called exlicitly", 100)
else:
    d_print(f"{__file__} imported by {__name__}", 100)
