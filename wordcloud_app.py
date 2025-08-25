import dash
from dash import dcc, html, Input, Output, callback
import pandas as pd
import re
from wordcloud import WordCloud
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for web deployment

# Text cleaning function
def clean_text_column(df, column_name):
    def clean_text(text):
        if pd.isnull(text):
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Replace double hyphens with space
        text = text.replace("--", " ")
        
        # Replace hyphens with spaces
        text = text.replace("-", " ")
        
        # Change spaces to underscores
        text = text.replace(" ", "_")
        
        # Remove leading and trailing spaces
        text = text.strip()
        
        # Remove all punctuation except semicolons
        text = re.sub(r'[^\w\s;]', '', text)
        
        # Replace ";_" with space
        text = text.replace(";_", " ")
        
        # Remove leading and trailing spaces
        text = text.strip()
        
        # Remove stop words
        stop_words = set(["the", "a", "an", "and", "or", "but", "if", "or", "because", "as", "what", "which", "when", "how", "all", "any", "both", "each", "few",
                          "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now", "in", "of"])
        words = text.split()
        filtered_words = [word for word in words if word not in stop_words]
        text = ' '.join(filtered_words)
        
        # Remove leading and trailing spaces
        text = text.strip()
        
        # Remove repeating words
        words = text.split()
        seen = set()
        unique_words = []
        for word in words:
            if word not in seen:
                seen.add(word)
                unique_words.append(word)
        
        return ' '.join(unique_words)
    
    # Apply the function to the column
    df[column_name] = df[column_name].apply(clean_text)
    return df

# Load and prepare data (you'll need to upload your CSV file)
def load_data():
    try:
        # Try to load the data file
        df = pd.read_csv('physical_usage.csv')  # Update path as needed
        
        # Create subset with required columns
        sub_and_code = df[['LC Classification Code', 'Subjects', 'Loans (In House + Not In House)']].copy()
        
        # Clean the data
        clean_df = clean_text_column(sub_and_code, "Subjects")
        clean_df['LC Classification Code'] = clean_df['LC Classification Code'].astype(str)
        clean_df['Loans (In House + Not In House)'] = clean_df['Loans (In House + Not In House)'].fillna(0).astype(int)
        
        return clean_df
    
    except FileNotFoundError:
        # Create sample data if file not found
        sample_data = {
            'LC Classification Code': ['M', 'HG', 'PQ', 'PT', 'BJ'] * 20,
            'Subjects': [
                'music classical piano', 'economics finance banking', 
                'literature french poetry', 'german literature fiction',
                'ethics philosophy morality'
            ] * 20,
            'Loans (In House + Not In House)': [1, 2, 3, 1, 4] * 20
        }
        return pd.DataFrame(sample_data)

# Initialize the Dash app
app = dash.Dash(__name__)
app.title = "Library Word Cloud Visualizer"

# Load data
try:
    clean_df = load_data()
    lc_codes = sorted(clean_df['LC Classification Code'].unique())
except Exception as e:
    # Fallback sample data
    sample_data = {
        'LC Classification Code': ['M', 'HG', 'PQ', 'PT', 'BJ'],
        'Subjects': [
            'music classical piano symphony orchestra',
            'economics finance banking monetary policy',
            'literature french poetry novels drama',
            'german literature fiction novels poetry',
            'ethics philosophy morality conduct behavior'
        ],
        'Loans (In House + Not In House)': [5, 3, 8, 2, 6]
    }
    clean_df = pd.DataFrame(sample_data)
    lc_codes = sorted(clean_df['LC Classification Code'].unique())

# App layout
app.layout = html.Div([
    html.Div([
        html.H1("Library Subject Word Cloud", 
                style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '30px'}),
        html.P("Explore library subjects by Library of Congress Classification codes", 
               style={'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': '16px'})
    ], style={'padding': '20px'}),
    
    html.Div([
        html.Label("Select LC Classification Code:", 
                  style={'fontWeight': 'bold', 'marginBottom': '10px', 'display': 'block'}),
        dcc.Dropdown(
            id='lc-dropdown',
            options=[{"label": f"{code} ({len(clean_df[clean_df['LC Classification Code'] == code])} items)", 
                     "value": code} for code in lc_codes],
            value=lc_codes[0] if lc_codes else None,
            clearable=False,
            style={'marginBottom': '20px'}
        )
    ], style={'maxWidth': '600px', 'margin': '0 auto', 'padding': '0 20px'}),
    
    html.Div([
        html.Img(id='wordcloud-img', style={'width': '100%', 'height': 'auto', 'maxWidth': '800px'})
    ], style={'textAlign': 'center', 'padding': '20px'}),
    
    html.Div([
        html.H3("Top Subjects", style={'color': '#2c3e50'}),
        html.Div(id='subject-list')
    ], style={'maxWidth': '800px', 'margin': '20px auto', 'padding': '0 20px'})
    
], style={'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#ecf0f1', 'minHeight': '100vh'})

# Callback to update word cloud
@callback(
    [Output('wordcloud-img', 'src'),
     Output('subject-list', 'children')],
    [Input('lc-dropdown', 'value')]
)
def update_wordcloud(selected_lc):
    if not selected_lc:
        return "", "No data available"
    
    # Filter data for selected LC code
    filtered_df = clean_df[clean_df["LC Classification Code"] == selected_lc]
    
    if filtered_df.empty:
        return "", "No data available for this classification code"
    
    # Create text for word cloud
    filtered_text = " ".join(filtered_df["Subjects"].fillna(""))
    
    if not filtered_text.strip():
        return "", "No subject data available for this classification code"
    
    # Generate word cloud
    try:
        wordcloud = WordCloud(
            width=800, 
            height=400, 
            background_color='white',
            colormap='viridis',
            max_words=100,
            relative_scaling=0.5,
            min_font_size=10
        ).generate(filtered_text)
        
        # Convert to image and encode as base64
        buf = BytesIO()
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.tight_layout(pad=0)
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
        plt.close()
        data = base64.b64encode(buf.getbuffer()).decode("utf8")
        img_src = f"data:image/png;base64,{data}"
        
    except Exception as e:
        return "", f"Error generating word cloud: {str(e)}"
    
    # Create subject list
    top_subjects = filtered_df.nlargest(10, 'Loans (In House + Not In House)')
    subject_items = []
    for _, row in top_subjects.iterrows():
        subject_items.append(
            html.Div([
                html.Span(row['Subjects'][:100] + "..." if len(row['Subjects']) > 100 else row['Subjects'], 
                         style={'fontWeight': 'bold'}),
                html.Span(f" ({row['Loans (In House + Not In House)']} loans)", 
                         style={'color': '#7f8c8d', 'marginLeft': '10px'})
            ], style={'marginBottom': '8px', 'padding': '5px', 'backgroundColor': 'white', 'borderRadius': '3px'})
        )
    
    return img_src, subject_items

# For deployment
server = app.server

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)