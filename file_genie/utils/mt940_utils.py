import zipfile
import io


def join_mt940_statements(zip_file_content) -> str:
    """
        Rearrange MT940 files contents based on 60M and 62M tags. 60M is the opening balance of a split
        statement and 62M is closing balance of a split statement. This function concat all such statements based on
        62M of the previous statement should be equal to the 60M of the next statement.

        Parameters:
            zip_file_content : The content to the ZIP file containing MT940 files.
    """
    with zipfile.ZipFile(io.BytesIO(zip_file_content.read())) as zip_file:
        first_file = []
        output_file_name = ""
        files_content_mapping_60M = {}

        for file_name in zip_file.namelist():
            with zip_file.open(file_name) as file:
                output_file_name = file_name
                file_content = file.readlines()
                fifth_line = file_content[4].decode('iso-8859-1').strip()
                if fifth_line is None or len(fifth_line) == 0:
                    return ""
                elif len(find_tag_value(':60F:', file_content)) > 0:
                    first_file = file_content
                elif len(find_tag_value(':60M:', file_content)) > 0:
                    inter_opening_balance_tag = find_tag_value(':60M:', file_content)
                    inter_opening_balance = inter_opening_balance_tag[len(":60M:"):].strip()
                    files_content_mapping_60M[inter_opening_balance] = file_content

        if first_file is None or len(first_file) == 0:
            return ""

        concat_statement = first_file

        while ':62F:' not in concat_statement[-2].decode('iso-8859-1').strip():
            second_last_line = concat_statement[-2].decode('iso-8859-1').strip()
            if ':62M:' in second_last_line:
                inter_closing_balance = second_last_line[len(':62M:'):]
                if inter_closing_balance not in files_content_mapping_60M:
                    break
                next_file_contents = files_content_mapping_60M.get(inter_closing_balance)
                concat_statement = concat_statement[:-2]
                concat_statement.extend(next_file_contents)
            else:
                break

    with open(output_file_name, 'wb') as file:
        for mt940_entry in concat_statement:
            file.write(mt940_entry)

    return output_file_name


def find_tag_value(tag, file_content):
    for line_no in range(10):
        line = file_content[line_no].decode('iso-8859-1').strip()
        if tag in line:
            return line
    return ""
