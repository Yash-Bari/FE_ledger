# pdf_extractor.py
import pdfplumber
import pandas as pd
import re
import os

# Function to extract tables directly from PDF
def extract_tables_from_pdf(pdf_path):
    all_students_data = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                print(f"Processing page {page_num} of {len(pdf.pages)}...")
                
                # Extract text to find student headers
                page_text = page.extract_text()
                
                # Find all student entries on this page - improved pattern
                prn_pattern = re.compile(r"PRN:(\S+)\s+SEAT NO.:(\S+)\s+NAME:([^\n]+?)(?:\s+Mother(?:Name)?[\s-]*([^\n]*))?(?:\s+Semester|First\s+Semester|\s*\n)", re.DOTALL | re.IGNORECASE)
                prn_matches = list(prn_pattern.finditer(page_text))
                
                for i, match in enumerate(prn_matches):
                    # Extract basic student information
                    prn = match.group(1)
                    seat_no = match.group(2)
                    name = match.group(3).strip()
                    mother_name = match.group(4).strip() if match.group(4) else ""
                    
                    # Find the student's text section
                    start_pos = match.start()
                    end_pos = prn_matches[i+1].start() if i < len(prn_matches) - 1 else len(page_text)
                    student_text = page_text[start_pos:end_pos]
                    
                    # Extract semester information - updated pattern
                    semester_pattern = re.compile(r"Semester\s*:\s*(\d+)", re.IGNORECASE)
                    semester_match = semester_pattern.search(student_text)
                    semester = semester_match.group(1) if semester_match else ""
                    
                    # Extract SGPA and credits info - updated patterns
                    sgpa_pattern = re.compile(r"First Semester SGPA\s*:\s*([\d.-]+|-----)")
                    sgpa_match = sgpa_pattern.search(student_text)
                    sgpa = sgpa_match.group(1) if sgpa_match else "N/A"
                    
                    credits_pattern = re.compile(r"Credits Earned/Total\s*:\s*(\d+/\d+)")
                    credits_match = credits_pattern.search(student_text)
                    credits_earned = credits_match.group(1) if credits_match else ""
                    
                    total_points_pattern = re.compile(r"Total Credit Points\s*:\s*(\d+)")
                    total_points_match = total_points_pattern.search(student_text)
                    total_credit_points = total_points_match.group(1) if total_points_match else ""
                    
                    # Parse subject data more precisely with improved function
                    subjects_data = parse_subjects_from_text(student_text)
                    
                    # Create student data dictionary
                    student_data = {
                        "PRN": prn,
                        "Seat No": seat_no,
                        "Name": name,
                        "Mother Name": mother_name,
                        "Semester": semester,
                        "SGPA": sgpa,
                        "Credits Earned/Total": credits_earned,
                        "Total Credit Points": total_credit_points,
                        **subjects_data
                    }
                    
                    all_students_data.append(student_data)
        
        print(f"Total students processed from PDF: {len(all_students_data)}")
        return all_students_data
                    
    except Exception as e:
        print(f"Error processing PDF tables: {str(e)}")
        return []

def parse_subjects_from_text(student_text):
    subjects_data = {}
    
    # Split into lines and find subject lines
    lines = student_text.strip().split("\n")
    subject_lines = []
    
    # Find subject lines (they start with course codes like AEC-101)
    for line in lines:
        line = line.strip()
        # Match standard subject code format
        if re.match(r"^[A-Z]{3}-\d+(?:-[A-Z]{3})?(?:-\d+)?(?:_TW)?", line):
            subject_lines.append(line)
    
    # Track keys that have been added to avoid duplicates
    added_keys = set()
    
    # For each subject line, extract the data using a more precise approach
    for line in subject_lines:
        parts = re.split(r'\s+', line)
        if len(parts) < 3:  # Need at least subject code and some data
            continue
        
        # Extract subject code (first part)
        subject_code = parts[0]
        
        # Check if this looks like a TW (Term Work) line
        is_tw_line = "_TW" in subject_code
        
        # If it's a TW line, we need to handle it differently
        if is_tw_line:
            # Extract the base subject code without the _TW suffix
            base_subject_code = subject_code.replace("_TW", "")
            # Use a different prefix for these columns
            column_prefix = f"{base_subject_code}_TW"
        else:
            column_prefix = subject_code
        
        # Prepare to extract values
        cce = "N/A"
        ese = "N/A"
        tw = "N/A"
        tot = "N/A"
        crd = "N/A"
        ern_crd = "N/A"
        grd = "N/A"
        grd_pnt = "N/A"
        crd_pnt = "N/A"
        
        try:
            # Find positions of key markers in the line
            # Look for grade values which are distinct patterns
            grade_patterns = ["A+", "A", "B+", "B", "C+", "C", "D", "E", "F", "O", "FFF"]
            grade_index = -1
            for i, part in enumerate(parts):
                if part in grade_patterns:
                    grade_index = i
                    grd = part
                    break
            
            if grade_index > 0:
                # Work backwards and forwards from grade to get other values
                # Typically grade is followed by grade point and credit point
                if grade_index + 1 < len(parts) and parts[grade_index + 1].isdigit():
                    grd_pnt = parts[grade_index + 1]
                
                if grade_index + 2 < len(parts) and parts[grade_index + 2].isdigit():
                    crd_pnt = parts[grade_index + 2]
                
                # Credits earned is typically right before grade
                if grade_index - 1 >= 0:
                    ern_crd = parts[grade_index - 1]
                
                # Credit is typically 2 positions before grade
                if grade_index - 2 >= 0:
                    crd = parts[grade_index - 2]
                
                # Total is typically 3 positions before grade, but could be "---"
                if grade_index - 3 >= 0:
                    tot = parts[grade_index - 3]
                    if tot.startswith('*'):
                        tot = tot[1:]  # Remove asterisk
                
                # Now work backwards to find ESE, CCE, TW
                # Look for numeric values or "---" in earlier positions
                
                # We'll extract the first few elements after subject code
                # that are either numeric or "---"
                value_indices = []
                for i in range(1, min(grade_index, len(parts))):
                    value = parts[i].replace('*', '')
                    if value.isdigit() or value == "---":
                        value_indices.append(i)
                
                # Based on the format in your data, assign values
                if len(value_indices) >= 1:
                    idx = value_indices[0]
                    cce = parts[idx].replace('*', '')
                    if parts[idx].startswith('*'):
                        cce = f"*{cce}"
                
                if len(value_indices) >= 2:
                    idx = value_indices[1]
                    ese = parts[idx].replace('*', '')
                    if parts[idx].startswith('*'):
                        ese = f"*{ese}"
                
                if len(value_indices) >= 3:
                    idx = value_indices[2]
                    tw = parts[idx].replace('*', '')
                    if parts[idx].startswith('*'):
                        tw = f"*{tw}"
            
            # If we didn't find a grade pattern, try a simpler approach
            else:
                # Look for numeric values
                numeric_indices = []
                for i, part in enumerate(parts):
                    clean_part = part.replace('*', '')
                    if clean_part.isdigit() or clean_part == "---":
                        numeric_indices.append(i)
                
                if len(numeric_indices) >= 3:
                    # Assume standard order: CCE, ESE, TW, TOT, etc.
                    cce_idx = numeric_indices[0]
                    ese_idx = numeric_indices[1]
                    tw_idx = numeric_indices[2]
                    
                    cce = parts[cce_idx].replace('*', '')
                    ese = parts[ese_idx].replace('*', '')
                    tw = parts[tw_idx].replace('*', '')
                    
                    # Check for asterisks in original values
                    if parts[cce_idx].startswith('*'):
                        cce = f"*{cce}"
                    if parts[ese_idx].startswith('*'):
                        ese = f"*{ese}"
                    if parts[tw_idx].startswith('*'):
                        tw = f"*{tw}"
        
        except Exception as e:
            print(f"Error parsing subject line: {line}")
            print(f"Error details: {str(e)}")
        
        # Create the keys using the appropriate prefix
        keys_to_store = {
            f"{column_prefix}_CCE": cce,
            f"{column_prefix}_ESE": ese,
            f"{column_prefix}_TW": tw,
            f"{column_prefix}_TOT": tot,
            f"{column_prefix}_CRD": crd,
            f"{column_prefix}_ERN_CRD": ern_crd,
            f"{column_prefix}_GRD": grd,
            f"{column_prefix}_GRD_PNT": grd_pnt,
            f"{column_prefix}_CRD_PNT": crd_pnt
        }
        
        # Add keys to subjects_data only if they don't already exist
        for key, value in keys_to_store.items():
            if key not in added_keys:
                subjects_data[key] = value
                added_keys.add(key)
            else:
                # For duplicate keys, append a numeric suffix
                i = 1
                new_key = f"{key}_{i}"
                while new_key in added_keys:
                    i += 1
                    new_key = f"{key}_{i}"
                subjects_data[new_key] = value
                added_keys.add(new_key)
    
    return subjects_data


def save_to_excel(data_list, output_file):
    if not data_list:
        print("No data to save to Excel.")
        return None
        
    # Handle missing columns across all students by finding all possible columns
    all_keys = set()
    for student_data in data_list:
        all_keys.update(student_data.keys())
    
    # Ensure all students have all columns (even if empty)
    for student_data in data_list:
        for key in all_keys:
            if key not in student_data:
                student_data[key] = None
    
    # Convert to DataFrame and save
    df = pd.DataFrame(data_list)
    
    # Fix duplicate columns BEFORE creating DataFrame
    all_columns = list(all_keys)
    
    # Find and handle duplicate column names
    seen_columns = set()
    column_counts = {}
    
    for i, col in enumerate(all_columns):
        if col in seen_columns:
            # This is a duplicate, rename it with a suffix
            if col not in column_counts:
                column_counts[col] = 1
            column_counts[col] += 1
            # Create a new column name with a suffix
            new_col = f"{col}_{column_counts[col]}"
            
            # Update the column name in all dictionaries
            for student_data in data_list:
                if col in student_data:
                    # Create a copy with the new name
                    student_data[new_col] = student_data[col]
                    # Remove the duplicate key
                    # We'll keep the first occurrence and rename all others
                    if column_counts[col] > 1:
                        student_data.pop(col, None)
        else:
            seen_columns.add(col)
    
    # Convert to DataFrame after fixing duplicate columns
    df = pd.DataFrame(data_list)
    
    # Reorder columns to put basic info first
    base_columns = ["PRN", "Seat No", "Name", "Mother Name", "Semester", "SGPA", 
                    "Credits Earned/Total", "Total Credit Points"]
    other_columns = [col for col in df.columns if col not in base_columns]
    
    # Sort the subject columns for better organization
    other_columns.sort()
    
    # Group columns by subject code
    subject_codes = set()
    for col in other_columns:
        parts = col.split('_')
        if len(parts) >= 2:
            subject_codes.add(parts[0])
    
    # Reorder columns by grouping them by subject
    ordered_other_columns = []
    for subject in sorted(subject_codes):
        subject_cols = [col for col in other_columns if col.startswith(subject)]
        # Sort within each subject group: CCE, ESE, TW, TOT, etc.
        col_order = ["_CCE", "_ESE", "_TW", "_TOT", "_CRD", "_ERN_CRD", "_GRD", "_GRD_PNT", "_CRD_PNT"]
        # Use a safer sorting method
        ordered_subject_cols = []
        for suffix in col_order:
            for col in subject_cols:
                if col.endswith(suffix) or any(col.endswith(f"{suffix}_{i}") for i in range(1, 10)):
                    ordered_subject_cols.append(col)
        
        # Add any remaining columns that might not match the expected patterns
        remaining_cols = [col for col in subject_cols if col not in ordered_subject_cols]
        ordered_subject_cols.extend(remaining_cols)
        
        ordered_other_columns.extend(ordered_subject_cols)
    
    # Final column order
    final_columns = base_columns + ordered_other_columns
    
    # Use only columns that exist in the dataframe
    existing_columns = [col for col in final_columns if col in df.columns]
    df = df[existing_columns]
    
    # Double-check for any remaining duplicate columns
    if len(df.columns) != len(set(df.columns)):
        # Find duplicates if any remain
        duplicates = [col for col in df.columns if list(df.columns).count(col) > 1]
        # Rename duplicates with numbered suffixes
        for dup in duplicates:
            dups = [i for i, col in enumerate(df.columns) if col == dup]
            # Keep the first occurrence, rename others
            for i, idx in enumerate(dups[1:], 1):
                df.columns.values[idx] = f"{dup}_{i}"
    
    # Remove any duplicate rows based on PRN
    df.drop_duplicates(subset=["PRN"], keep="first", inplace=True)
    
    try:
        df.to_excel(output_file, index=False)
        print(f"Data saved successfully to {output_file}")
        print(f"Total number of students processed: {len(df)}")
    except Exception as e:
        print(f"Error saving Excel file: {str(e)}")
    
    return df