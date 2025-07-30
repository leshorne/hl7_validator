import re

class HL7MessageToDict:
    def __init__(self, input_str: str):
        self.hl7_message = input_str

    def _unescape_hl7_value(self, value: str, field_del: str, comp_del: str, rep_del: str, esc_char: str,
                            sub_comp_del: str) -> str:
        """
        Replaces common HL7v2 escape sequences with their actual characters.

        Args:
            value: The string containing potential HL7v2 escape sequences.
            field_del: The field delimiter character.
            comp_del: The component delimiter character.
            rep_del: The repetition delimiter character.
            esc_char: The escape character.
            sub_comp_del: The subcomponent delimiter character.

        Returns:
            The unescaped string.
        """
        # This helper function remains unchanged as it is still necessary.
        value = value.replace(esc_char + esc_char, esc_char)
        value = value.replace(esc_char + 'F' + esc_char, field_del)
        value = value.replace(esc_char + 'S' + esc_char, comp_del)
        value = value.replace(esc_char + 'R' + esc_char, rep_del)
        value = value.replace(esc_char + 'E' + esc_char, esc_char)
        value = value.replace(esc_char + 'T' + esc_char, sub_comp_del)
        return value


    def parse_hl7_message(self) -> dict:
        """
        Parses an HL7v2 message string into a nested dictionary.

        The returned dictionary is structured with segment names as top-level keys
        (e.g., "MSH", "PID"). Each key holds a dictionary for that segment's data.
        If a segment repeats (e.g., OBX), the key will hold a list of dictionaries.

        Within each segment's dictionary, keys are based on HL7 field notation
        (e.g., '3-1' for the first component of the third field). If a field
        repeats, an index is added (e.g., '13[1]-1', '13[2]-1').

        Args:
            hl7_message: The HL7v2 message string.

        Returns:
            A nested dictionary representing the parsed HL7 message.
        """
        hl7_message = self.hl7_message

        parsed_data = {}

        # Default delimiters
        field_delimiter = '|'
        component_delimiter = '^'
        repetition_delimiter = '~'
        escape_character = '\\'
        subcomponent_delimiter = '&'

        segments = re.split(r'[\r\n]+', hl7_message.strip())

        # --- First Pass: Identify Delimiters from MSH Segment ---
        msh_segment_line = next((s for s in segments if s.startswith('MSH')), None)

        if msh_segment_line:
            if len(msh_segment_line) > 3:
                field_delimiter = msh_segment_line[3]
            if len(msh_segment_line) >= 8:
                encoding_chars = msh_segment_line[4:8]
                component_delimiter = encoding_chars[0]
                repetition_delimiter = encoding_chars[1]
                escape_character = encoding_chars[2]
                subcomponent_delimiter = encoding_chars[3]

        # --- Second Pass: Process Each Segment ---
        for segment_line in segments:
            if not segment_line.strip():
                continue

            fields = segment_line.split(field_delimiter)
            raw_segment_name = fields[0]
            segment_dict = {}  # Create a new dictionary for this specific segment

            current_field_list = []
            current_hl7_field_start_idx = 0

            if raw_segment_name == 'MSH':
                # MSH-1 is the field delimiter, MSH-2 is the encoding characters
                segment_dict['MSH-1'] = field_delimiter
                if len(fields) > 1:
                    segment_dict['MSH-2'] = fields[1]
                current_field_list = fields[2:]
                current_hl7_field_start_idx = 3
            else:
                current_field_list = fields[1:]
                current_hl7_field_start_idx = 1

            for field_idx_offset, field_value in enumerate(current_field_list):
                hl7_field_number = current_hl7_field_start_idx + field_idx_offset
                repetitions = field_value.split(repetition_delimiter)

                for rep_idx, rep_value in enumerate(repetitions, start=1):
                    components = rep_value.split(component_delimiter)

                    for comp_idx, comp_value in enumerate(components, start=1):
                        subcomponents = comp_value.split(subcomponent_delimiter)

                        for sub_comp_idx, sub_comp_value in enumerate(subcomponents, start=1):
                            # Build the key relative to the segment (e.g., 'MSH-3', 'MSH-3-1', 'PID-13[1]')
                            field_key = f'{raw_segment_name}-{hl7_field_number}'
                            if len(repetitions) > 1:
                                field_key += f'[{rep_idx}]'

                            key_parts = [field_key]

                            # Add component index if needed
                            add_comp_index = (component_delimiter in rep_value or len(components) > 1 or
                                              (len(components) == 1 and (
                                                          subcomponent_delimiter in comp_value or len(subcomponents) > 1)))
                            if add_comp_index:
                                key_parts.append(str(comp_idx))

                                # Add sub-component index if needed
                                add_sub_comp_index = subcomponent_delimiter in comp_value or len(subcomponents) > 1
                                if add_sub_comp_index:
                                    key_parts.append(str(sub_comp_idx))

                            final_key = '-'.join(key_parts)

                            unescaped_value = self._unescape_hl7_value(
                                sub_comp_value, field_delimiter, component_delimiter,
                                repetition_delimiter, escape_character, subcomponent_delimiter
                            )
                            segment_dict[final_key] = unescaped_value

            # Add the populated segment dictionary to the main parsed_data
            if raw_segment_name not in parsed_data:
                # First time seeing this segment, store its dictionary
                parsed_data[raw_segment_name] = segment_dict
            else:
                # This segment is repeating, convert to a list if it's not already one
                if not isinstance(parsed_data[raw_segment_name], list):
                    # This is the second occurrence, so create a list with the first and second items
                    parsed_data[raw_segment_name] = [parsed_data[raw_segment_name], segment_dict]
                else:
                    # It's already a list, just append the new segment dictionary
                    parsed_data[raw_segment_name].append(segment_dict)

        return parsed_data
