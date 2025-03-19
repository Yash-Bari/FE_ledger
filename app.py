import streamlit as st
import pandas as pd
import os
import time
import base64
from io import BytesIO
import tempfile
import plotly.express as px

# Import backend functions
from pdf_extractor import extract_tables_from_pdf, save_to_excel

# Set page configuration
st.set_page_config(
    page_title="Student Data Extractor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        font-weight: 700;
        margin-bottom: 1rem;
        text-align: center;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #4CAF50;
    }
    .process-box {
        background-color: #E3F2FD;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #2196F3;
        margin-bottom: 1rem;
    }
    .stProgress > div > div > div > div {
        background-color: #1E88E5;
    }
    .upload-section {
        border: 2px dashed #BDBDBD;
        border-radius: 0.5rem;
        padding: 2rem;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stats-card {
        background-color: #F5F5F5;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .download-btn {
        background-color: #4CAF50;
        color: white;
        padding: 0.5rem 1rem;
        text-decoration: none;
        border-radius: 0.3rem;
        font-weight: bold;
        display: inline-block;
        margin-top: 1rem;
    }
    .download-btn:hover {
        background-color: #45a049;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Modified get_excel_download_link function
def get_excel_download_link(df, filename="students_data.xlsx"):
    """Generate a download link for the excel file"""
    output = BytesIO()
    
    # Use the context manager approach which handles the saving properly
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='StudentData')
    
    processed_data = output.getvalue()
    b64 = base64.b64encode(processed_data).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}" class="download-btn">Download Excel File</a>'
    return href

# Animated progress function
def progress_bar_with_animation(text, num_steps=10):
    """Display an animated progress bar"""
    progress_text = st.empty()
    progress_bar = st.progress(0)
    
    for i in range(num_steps+1):
        progress_text.text(f"{text} ({i*10}%)")
        progress_bar.progress(i/num_steps)
        time.sleep(0.1)
    
    progress_text.empty()
    progress_bar.empty()

# Function to create a placeholder animation while processing
def processing_animation():
    """Show processing animation"""
    with st.spinner("Processing your PDF file..."):
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            processing_placeholder = st.empty()
            for i in range(5):
                for dots in ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]:
                    processing_placeholder.markdown(f"<div style='text-align: center; font-size: 2rem;'>Processing {dots}</div>", unsafe_allow_html=True)
                    time.sleep(0.1)
            processing_placeholder.empty()

# Function to show statistics
def show_statistics(df):
    """Display statistics about the extracted data"""
    st.markdown("<h3 class='sub-header'>📈 Data Statistics</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("<div class='stats-card'>", unsafe_allow_html=True)
        st.metric("Total Students", len(df))
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='stats-card'>", unsafe_allow_html=True)
        # Handle SGPA calculation more carefully
        try:
            # Convert SGPA to numeric, coercing errors to NaN
            numeric_sgpa = pd.to_numeric(df['SGPA'].replace('-----', pd.NA), errors='coerce')
            # Calculate mean only if there are valid values
            if not numeric_sgpa.isna().all():
                avg_sgpa = numeric_sgpa.mean()
                st.metric("Average SGPA", f"{avg_sgpa:.2f}")
            else:
                st.metric("Average SGPA", "N/A")
        except Exception as e:
            st.metric("Average SGPA", "N/A")
            print(f"SGPA calculation error: {str(e)}")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<div class='stats-card'>", unsafe_allow_html=True)
        # Get all subject columns that contain grades
        grade_cols = [col for col in df.columns if '_GRD' in col]
        total_subjects = len(grade_cols)
        st.metric("Total Subjects", total_subjects)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Create a simple visualization for SGPA distribution
    try:
        # Convert SGPA to numeric, coercing errors to NaN
        sgpa_data = pd.to_numeric(df['SGPA'].replace(['-----', 'N/A'], pd.NA), errors='coerce')
        sgpa_data = sgpa_data.dropna()
        
        if not sgpa_data.empty and len(sgpa_data) > 1:
            fig = px.histogram(
                sgpa_data,
                nbins=10,
                labels={'value': 'SGPA', 'count': 'Number of Students'},
                title='SGPA Distribution',
                color_discrete_sequence=['#1E88E5']
            )
            fig.update_layout(
                xaxis_title="SGPA",
                yaxis_title="Number of Students",
                bargap=0.1
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough valid SGPA data to create a distribution chart.")
    except Exception as e:
        st.info(f"Could not generate SGPA distribution chart: {str(e)}")

# Save extracted data to session state
def save_data_to_session_state(df):
    """Save DataFrame to session state for later use"""
    st.session_state['extracted_data'] = df

# Main app function
def main():
    # Initialize session state for storing extracted data
    if 'extracted_data' not in st.session_state:
        st.session_state['extracted_data'] = None
        st.session_state['processing_complete'] = False
    
    # Header
    st.markdown("<h1 class='main-header'>Student Data Extractor</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; margin-bottom: 2rem;'>Extract student data from PDF result sheets and convert to Excel</p>", unsafe_allow_html=True)
    
    # Sidebar information
    with st.sidebar:
        st.image("https://via.placeholder.com/150x150?text=PDF+To+Excel", width=150)
        st.markdown("### About")
        st.info(
            "This application extracts student data from PDF result sheets and converts it to Excel format. "
            "Upload your PDF file to get started."
        )
        
        st.markdown("### Instructions")
        st.markdown(
            """
            1. Upload your PDF result file
            2. Wait for the processing to complete
            3. Download the Excel file
            4. Review data statistics
            """
        )
        
        st.markdown("### Features")
        st.markdown(
            """
            - Extracts student information
            - Identifies subject grades and scores
            - Calculates SGPA and other metrics
            - Organized Excel output
            """
        )
    
    # File uploader
    st.markdown("<div class='upload-section'>", unsafe_allow_html=True)
    st.markdown("<h3 class='sub-header'>📄 Upload PDF Result File</h3>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
    st.markdown("</div>", unsafe_allow_html=True)
    
    if uploaded_file is not None:
        # Display file details
        file_details = {
            "Filename": uploaded_file.name,
            "File size": f"{uploaded_file.size / 1024:.2f} KB"
        }
        
        st.markdown("<div class='process-box'>", unsafe_allow_html=True)
        st.write("File Details:")
        for key, value in file_details.items():
            st.write(f"- **{key}:** {value}")
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            pdf_path = tmp_file.name
        
        # Process button
        if st.button("Process PDF", key="process_button"):
            try:
                # Show loading animation
                processing_animation()
                
                # Process the PDF file
                with st.spinner("Extracting data from PDF..."):
                    progress_bar_with_animation("Extracting student information", 10)
                    all_students_data = extract_tables_from_pdf(pdf_path)
                
                if not all_students_data:
                    st.error("No data could be extracted from the PDF. Please check the file format.")
                else:
                    # Save to Excel
                    excel_file = "students_data.xlsx"
                    with st.spinner("Saving data to Excel..."):
                        progress_bar_with_animation("Creating Excel file", 5)
                        df = save_to_excel(all_students_data, excel_file)
                    
                    # Store in session state
                    save_data_to_session_state(df)
                    st.session_state['processing_complete'] = True
                    
                    # Success message
                    st.markdown("<div class='success-box'>", unsafe_allow_html=True)
                    st.success(f"✅ Successfully extracted data for {len(df)} students!")
                    st.markdown(get_excel_download_link(df), unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Display statistics
                    show_statistics(df)
                    
                    # Preview the data
                    st.markdown("<h3 class='sub-header'>👁️ Data Preview</h3>", unsafe_allow_html=True)
                    st.dataframe(df.head(5), use_container_width=True)
                    
            except Exception as e:
                st.error(f"Error processing PDF: {str(e)}")
                import traceback
                st.error(traceback.format_exc())
            
            finally:
                # Remove the temporary file
                try:
                    os.unlink(pdf_path)
                except:
                    pass
    
    # Show download button if processing is already complete
    if st.session_state.get('processing_complete', False) and st.session_state.get('extracted_data') is not None:
        st.markdown("<div class='success-box'>", unsafe_allow_html=True)
        st.success("Your data has been processed and is ready for download!")
        st.markdown(get_excel_download_link(st.session_state['extracted_data']), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Display statistics for data in session state
        show_statistics(st.session_state['extracted_data'])
        
        # Preview the data
        st.markdown("<h3 class='sub-header'>👁️ Data Preview</h3>", unsafe_allow_html=True)
        st.dataframe(st.session_state['extracted_data'].head(5), use_container_width=True)

if __name__ == "__main__":
    main()