from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
import pandas as pd
import plotly.express as px
from plotly.offline import plot
from .models import DataFile

def gemini_ai_analysis(df):
    # Placeholder for detailed AI-based insights
    insights = []
    
    # Example analysis and insights
    if 'age' in df.columns:
        age_mean = df['age'].mean()
        age_std = df['age'].std()
        age_total = df['age'].sum()
        insights.append(f"Average age is {age_mean:.2f} years.")
        insights.append(f"Standard deviation of age is {age_std:.2f} years.")
        insights.append(f"Total sum of all ages is {age_total:.2f} years.")
    
    if 'gender' in df.columns:
        gender_counts = df['gender'].value_counts()
        gender_total = gender_counts.sum()
        insights.append(f"Gender distribution: {', '.join([f'{gender}: {count}' for gender, count in gender_counts.items()])}.")
        insights.append(f"Total count of all genders is {gender_total}.")
    
    if 'cause_of_death' in df.columns:
        cause_of_death_counts = df['cause_of_death'].value_counts()
        cause_of_death_total = cause_of_death_counts.sum()
        insights.append(f"Cause of death distribution: {', '.join([f'{cause}: {count}' for cause, count in cause_of_death_counts.items()])}.")
        insights.append(f"Total count of causes of death is {cause_of_death_total}.")
    
    if 'date' in df.columns:
        date_range = f"From {df['date'].min().date()} to {df['date'].max().date()}"
        insights.append(f"Data covers the period {date_range}.")
    
    # Combine insights into a single string
    if insights:
        ai_insights = "Insights based on the data:\n" + "\n".join(insights)
    else:
        ai_insights = "No specific insights available for the provided data."
    
    return ai_insights

def upload_file(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        # Check if the file type is supported (e.g., only Excel files)
        if file_extension not in ['xls', 'xlsx']:
            return render(request, 'analysis/upload.html', {
                'message': 'Unsupported file type. Please upload an Excel file.',
            })
        
        # Save the uploaded file
        fs = FileSystemStorage()
        filename = fs.save(uploaded_file.name, uploaded_file)
        
        # Store metadata about the file in the database
        data_file = DataFile(file_name=filename)
        data_file.save()
        
        # Load the Excel file into a Pandas DataFrame
        file_path = fs.path(filename)
        df = pd.read_excel(file_path)
        
        # Check if the DataFrame is empty
        if df.empty:
            return render(request, 'analysis/upload.html', {
                'message': 'The provided file does not contain any data.',
            })
        
        # Data Cleaning and Preparation
        summary_df = df.describe(include='all').transpose()
        
        # Ensure the desired columns exist
        required_columns = ['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']
        existing_columns = [col for col in required_columns if col in summary_df.columns]
        
        # Convert summary statistics to integers if there are no decimals
        for col in existing_columns:
            if pd.api.types.is_numeric_dtype(summary_df[col]):
                if summary_df[col].apply(lambda x: x.is_integer() if pd.notnull(x) else False).all():
                    summary_df[col] = summary_df[col].astype('Int64')  # Use Int64 to keep NaNs
        
        # Filter only existing columns for display
        summary_df = summary_df[existing_columns]
        
        summary_html = summary_df.to_html(classes='table table-striped', border=0, justify='center')

        # Ensure 'age' column exists before proceeding
        if 'age' in df.columns:
            df['Age Category'] = pd.cut(df['age'], bins=[0, 12, 18, 35, 60, 100],
                                        labels=['Child', 'Teen', 'Adult', 'Middle Age', 'Senior'])
        else:
            df['Age Category'] = None
        
        # AI insights using updated function
        ai_insights = gemini_ai_analysis(df)
        
        # Visualizations
        graphs = {}

        # 1. Histogram (Age Distribution)
        if 'age' in df.columns:
            fig_histogram = px.histogram(df, x='age', title="Age Distribution")
            graphs['histogram'] = plot(fig_histogram, output_type='div')
        
        # 2. Bar Graph (Gender Distribution)
        if 'gender' in df.columns:
            gender_counts = df['gender'].value_counts()
            fig_bar = px.bar(x=gender_counts.index, y=gender_counts.values, labels={'x':'Gender', 'y':'Count'},
                             title="Gender Distribution")
            graphs['bar'] = plot(fig_bar, output_type='div')
        
        # 3. Pie Chart (Cause of Death Distribution)
        if 'cause_of_death' in df.columns:
            fig_pie = px.pie(df, names='cause_of_death', title="Cause of Death Distribution")
            graphs['pie'] = plot(fig_pie, output_type='div')
        
        # 4. Line Graph (Time Series Analysis)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            for column in df.columns:
                if column != 'date':
                    fig_line = px.line(df, x='date', y=column, title=f"Time Series Analysis of {column}")
                    graphs[f'line_{column}'] = plot(fig_line, output_type='div')
        
        return render(request, 'analysis/dashboard.html', {
            'summary': summary_html,
            'graphs': graphs,
            'ai_insights': ai_insights,
        })
    
    # Handle case where no file is provided
    return render(request, 'analysis/upload.html', {
        'message': 'Please upload a file.',
    })
