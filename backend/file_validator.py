"""
File Upload Validation Module
Validates Excel file uploads with comprehensive checks
"""

import os
import pandas as pd
from fastapi import HTTPException, UploadFile
from typing import Tuple, List, Dict

# Configuration
ALLOWED_EXTENSIONS = {'.xlsx', '.xls', '.csv'}
ALLOWED_MIMETYPES = {
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
    'application/vnd.ms-excel',  # .xls
    'text/csv',  # .csv
    'application/csv',  # .csv (alternative)
}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Required and optional columns
REQUIRED_COLUMNS = ['UPC']
OPTIONAL_COLUMNS = ['ITEM', 'BRAND', 'MARKETS', 'MPACK', 'FACTS', 'NRMSIZE']


def validate_file_type(file: UploadFile) -> bool:
    """
    Validate uploaded file is Excel or CSV format
    
    Args:
        file: FastAPI UploadFile object
        
    Returns:
        True if valid
        
    Raises:
        HTTPException: If file type is invalid
    """
    # Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Expected Excel or CSV file (.xlsx, .xls, or .csv), got '{file_ext}'. "
                   f"Please upload a valid file."
        )
    
    # Check MIME type (skip for CSV as browsers may send different MIME types)
    if file.content_type and file.content_type not in ALLOWED_MIMETYPES and file_ext != '.csv':
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format. Expected Excel or CSV file, got '{file.content_type}'. "
                   f"Please upload a valid file."
        )
    
    return True


def validate_file_size(contents: bytes) -> bool:
    """
    Validate file size is within limits
    
    Args:
        contents: File contents as bytes
        
    Returns:
        True if valid
        
    Raises:
        HTTPException: If file size is invalid
    """
    file_size = len(contents)
    
    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="File is empty. Please upload a valid Excel file with data."
        )
    
    if file_size > MAX_FILE_SIZE:
        size_mb = file_size / (1024 * 1024)
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.2f}MB). Maximum allowed size is {max_mb:.0f}MB. "
                   f"Please reduce file size or split into multiple files."
        )
    
    return True


def validate_excel_file(file_contents) -> pd.ExcelFile:
    """
    Validate file can be read as Excel
    
    Args:
        file_contents: BytesIO object with file contents
        
    Returns:
        pd.ExcelFile object if valid
        
    Raises:
        HTTPException: If Excel file is invalid
    """
    try:
        xl = pd.ExcelFile(file_contents)
        
        # Check if file has sheets
        if not xl.sheet_names:
            raise HTTPException(
                status_code=400,
                detail="Excel file has no sheets. Please upload a valid Excel file with at least one sheet."
            )
        
        return xl
        
    except ValueError as e:
        error_msg = str(e)
        if "Excel file format" in error_msg:
            raise HTTPException(
                status_code=400,
                detail="Invalid Excel file format. The file may be corrupted or not a valid Excel file. "
                       "Please save the file again in Excel format (.xlsx or .xls) and try uploading."
            )
        raise HTTPException(
            status_code=400,
            detail=f"Cannot read Excel file: {error_msg}"
        )
        
    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=400,
            detail="Excel file is empty or contains no data. Please add data to the file and try again."
        )
        
    except Exception as e:
        error_msg = str(e)
        if "Workbook" in error_msg and "corrupt" in error_msg.lower():
            raise HTTPException(
                status_code=400,
                detail="Excel file appears to be corrupted. Please try opening and re-saving the file in Excel, "
                       "then upload again."
            )
        raise HTTPException(
            status_code=400,
            detail=f"Cannot read Excel file. The file may be corrupted or in an unsupported format: {error_msg}"
        )


def validate_columns(df: pd.DataFrame, sheet_name: str) -> Tuple[Dict[str, str], List[str]]:
    """
    Validate required columns exist in DataFrame
    
    Args:
        df: pandas DataFrame
        sheet_name: Name of the sheet being validated
        
    Returns:
        Tuple of (column_map, warnings)
        
    Raises:
        HTTPException: If required columns are missing
    """
    col_map = {c.upper().strip(): c for c in df.columns}
    warnings = []
    
    # Check required columns
    missing_required = []
    for req_col in REQUIRED_COLUMNS:
        if req_col not in col_map:
            missing_required.append(req_col)
    
    if missing_required:
        available_cols = ', '.join([f"'{col}'" for col in df.columns[:10]])  # Show first 10
        if len(df.columns) > 10:
            available_cols += f", ... ({len(df.columns)} total columns)"
        
        raise HTTPException(
            status_code=400,
            detail=f"Sheet '{sheet_name}' is missing required column(s): {', '.join(missing_required)}. "
                   f"Available columns: {available_cols}. "
                   f"Please ensure your Excel file has a column named 'UPC'."
        )
    
    # Check for optional columns (warnings only)
    missing_optional = []
    for opt_col in OPTIONAL_COLUMNS:
        if opt_col not in col_map:
            missing_optional.append(opt_col)
    
    if missing_optional:
        warnings.append(
            f"Sheet '{sheet_name}': Optional columns not found: {', '.join(missing_optional)}. "
            f"Processing will continue but some features may be limited."
        )
    
    return col_map, warnings


def validate_data(df: pd.DataFrame, col_map: Dict[str, str], sheet_name: str) -> List[str]:
    """
    Validate data types and values in DataFrame
    
    Args:
        df: pandas DataFrame
        col_map: Mapping of uppercase column names to actual column names
        sheet_name: Name of the sheet being validated
        
    Returns:
        List of warning messages
        
    Raises:
        HTTPException: If data validation fails
    """
    warnings = []
    errors = []
    
    upc_col = col_map['UPC']
    
    # Check total rows
    total_rows = len(df)
    if total_rows == 0:
        errors.append(f"Sheet '{sheet_name}' has no data rows")
    
    # Check for empty UPC values
    null_upcs = df[upc_col].isnull().sum()
    valid_upcs = df[upc_col].notnull().sum()
    
    if null_upcs > 0:
        warnings.append(
            f"Sheet '{sheet_name}': {null_upcs} out of {total_rows} rows have empty UPC values "
            f"and will be skipped during processing"
        )
    
    # Check if ALL UPCs are empty
    if valid_upcs == 0:
        errors.append(
            f"Sheet '{sheet_name}': No valid UPC values found. All rows have empty UPC column. "
            f"Please ensure UPC column contains data."
        )
    
    # Check for duplicate UPCs (warning only)
    if valid_upcs > 0:
        duplicate_upcs = df[upc_col].duplicated().sum()
        if duplicate_upcs > 0:
            warnings.append(
                f"Sheet '{sheet_name}': {duplicate_upcs} duplicate UPC values found. "
                f"These will be merged according to the merging rules."
            )
    
    # Check for numeric columns (monthly data)
    monthly_cols = [c for c in df.columns if 
        any(m in str(c).upper() for m in ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", 
                                           "JUL", "AUG", "SEP", "OCT", "NOV", "DEC", "MAT", "W/E"])]
    
    if monthly_cols:
        non_numeric_cols = []
        for col in monthly_cols:
            # Try to convert to numeric
            try:
                numeric_vals = pd.to_numeric(df[col], errors='coerce')
                non_numeric_count = numeric_vals.isnull().sum() - df[col].isnull().sum()
                if non_numeric_count > 0:
                    non_numeric_cols.append(f"{col} ({non_numeric_count} non-numeric values)")
            except:
                non_numeric_cols.append(col)
        
        if non_numeric_cols:
            warnings.append(
                f"Sheet '{sheet_name}': Some monthly columns contain non-numeric values: "
                f"{', '.join(non_numeric_cols[:5])}. Non-numeric values will be treated as 0."
            )
    else:
        warnings.append(
            f"Sheet '{sheet_name}': No monthly data columns detected. "
            f"Expected columns with names like 'Jan 24', 'Feb 24', etc."
        )
    
    # Raise errors if any
    if errors:
        raise HTTPException(
            status_code=400,
            detail=f"Data validation failed: {'; '.join(errors)}"
        )
    
    return warnings


def validate_upload_file(file: UploadFile, contents: bytes) -> Tuple[pd.ExcelFile, List[str]]:
    """
    Comprehensive validation of uploaded Excel file
    
    Args:
        file: FastAPI UploadFile object
        contents: File contents as bytes
        
    Returns:
        Tuple of (ExcelFile object, list of warnings)
        
    Raises:
        HTTPException: If validation fails
    """
    import io
    
    all_warnings = []
    
    # Step 1: Validate file type
    validate_file_type(file)
    
    # Step 2: Validate file size
    validate_file_size(contents)
    
    # Step 3: Validate Excel file format
    xl = validate_excel_file(io.BytesIO(contents))
    
    # Step 4: Validate each sheet
    for sheet_name in xl.sheet_names:
        try:
            df = xl.parse(sheet_name)
            
            # Validate columns
            col_map, col_warnings = validate_columns(df, sheet_name)
            all_warnings.extend(col_warnings)
            
            # Validate data
            data_warnings = validate_data(df, col_map, sheet_name)
            all_warnings.extend(data_warnings)
            
        except HTTPException:
            # Re-raise validation errors
            raise
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error validating sheet '{sheet_name}': {str(e)}"
            )
    
    return xl, all_warnings
