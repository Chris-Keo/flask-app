from dash import Dash, html, dcc, Input, Output, callback, State, ALL, MATCH, no_update
import dash
import dash_daq as daq
import dash_ag_grid as dag
import logging
import functools
import time
import pandas as pd
from typing import List, Optional, Protocol, Dict, Any
from dataclasses import dataclass

class LoadingContainer(dcc.Loading):
    """
    Custom Loading container that inherits from dcc.Loading
    with integrated target_components support.
    """
    
    def __init__(self, children: List, styled: bool = True, target_components: Optional[Dict] = None):
        props = {}
        
        if styled:
            parent_style = {'border-radius': '8px', 'height': '100%'}
            props.update({'type': 'circle', 'parent_style': parent_style})
        
        if target_components:
            props['target_components'] = target_components

        super().__init__(children, **props)
    
    @property
    def target_components(self) -> List[str]:
        """Get the list of target component IDs."""
        return self._target_components
    
    @target_components.setter
    def target_components(self, value: List[str]) -> None:
        """Set the list of target component IDs."""
        if not isinstance(value, (list, tuple)):
            raise ValueError("target_components must be a list or tuple")
        self._target_components = list(value)
    
    def add_target_component(self, component_id: str) -> None:
        """Add a component ID to the target list."""
        if component_id not in self._target_components:
            self._target_components.append(component_id)
    
    def remove_target_component(self, component_id: str) -> None:
        """Remove a component ID from the target list."""
        if component_id in self._target_components:
            self._target_components.remove(component_id)
    
    def clear_target_components(self) -> None:
        """Clear all target components."""
        self._target_components.clear()


# Protocol for loading component configuration
class LoadingConfigProtocol(Protocol):
    """Protocol defining the structure for loading component configuration."""
    children: List[Any]
    styled: bool
    target_components: Optional[List[str]]
    type: str
    parent_style: Dict[str, str]


@dataclass
class LoadingConfig:
    """
    Dataclass for loading component configuration.
    """
    children: List[Any]
    styled: bool = True
    target_components: Optional[List[str]] = None
    type: str = "circle"
    parent_style: Dict[str, str] = None
    
    def __post_init__(self):
        """Post-initialization to set default parent_style if styled is True."""
        if self.styled and self.parent_style is None:
            self.parent_style = {'border-radius': '8px', 'height': '100%'}


class LoadingContainerDataclass(dcc.Loading):
    """
    Dataclass-based Loading container that inherits from dcc.Loading.
    Uses LoadingConfig dataclass for configuration.
    """
    
    def __init__(self, config: LoadingConfig, **kwargs):
        """
        Initialize the LoadingContainerDataclass.
        
        Args:
            config: LoadingConfig dataclass instance with configuration
            **kwargs: Additional props to pass to dcc.Loading
        """
        # Build props from config
        props = {
            'type': config.type,
            **kwargs
        }
        
        # Add parent_style if styled
        if config.styled and config.parent_style:
            props['parent_style'] = config.parent_style
        
        # Add target_components if specified
        if config.target_components:
            props['target_components'] = config.target_components
        
        super().__init__(config.children, **props)
    
    @classmethod
    def create(cls, children: List[Any], styled: bool = True, 
               target_components: Optional[List[str]] = None, **kwargs) -> 'LoadingContainerDataclass':
        """
        Factory method to create LoadingContainerDataclass with configuration.
        
        Args:
            children: List of child components
            styled: Whether to apply default styling
            target_components: List of component IDs to target
            **kwargs: Additional configuration options
        
        Returns:
            LoadingContainerDataclass instance
        """
        config = LoadingConfig(
            children=children,
            styled=styled,
            target_components=target_components,
            **kwargs
        )
        return cls(config)

# Initialize the Dash app
app = Dash(__name__)

# Add custom CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            /* Style for the switch track (background) */
            .dark-theme-control .switch-track {
                background-color: #4a4a4a !important;  /* Track color when OFF */
                border: 2px solid #666666 !important;
            }
            
            /* Style for the switch track when ON */
            .dark-theme-control .switch-track--checked {
                background-color: #007439 !important;  /* Track color when ON */
                border-color: #00EA64 !important;
            }
            
            /* Style for the toggle handle (the moving part) */
            .dark-theme-control .switch-handle {
                background-color: #ffffff !important;  /* Handle color when OFF */
                border: 2px solid #00EA64 !important;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
            }
            
            /* Style for the toggle handle when ON */
            .dark-theme-control .switch-handle--checked {
                background-color: #00EA64 !important;  /* Handle color when ON */
                border-color: #007439 !important;
            }
            
            /* Hover effects */
            .dark-theme-control:hover .switch-track {
                background-color: #666666 !important;
            }
            
            .dark-theme-control:hover .switch-track--checked {
                background-color: #008844 !important;
            }
            
            .dark-theme-control:hover .switch-handle {
                box-shadow: 0 4px 8px rgba(0,0,0,0.3) !important;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dash_callbacks.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Sample data for AG Grid
sample_data = [
    {"id": 1, "name": "Alice Johnson", "age": 28, "department": "Engineering", "salary": 75000},
    {"id": 2, "name": "Bob Smith", "age": 34, "department": "Marketing", "salary": 65000},
    {"id": 3, "name": "Carol Davis", "age": 29, "department": "Engineering", "salary": 80000},
    {"id": 4, "name": "David Wilson", "age": 31, "department": "Sales", "salary": 70000},
    {"id": 5, "name": "Eva Brown", "age": 26, "department": "HR", "salary": 55000},
    {"id": 6, "name": "Frank Miller", "age": 35, "department": "Engineering", "salary": 85000},
    {"id": 7, "name": "Grace Lee", "age": 27, "department": "Marketing", "salary": 60000},
    {"id": 8, "name": "Henry Taylor", "age": 33, "department": "Sales", "salary": 72000},
]

# Define theme styles
light_theme = {
    'dark': False,
    'detail': '#007439',
    'primary': '#00EA64',
    'secondary': '#6E6E6E',
    'backgroundColor': '#ffffff',
    'textColor': '#000000',
    'componentBackgroundColor': '#f8f9fa',
    'borderColor': '#e0e0e0',
    'disabledColor': '#cccccc',
    'disabledTextColor': '#666666',
    'successColor': '#28a745',
    'warningColor': '#ffc107',
    'dangerColor': '#dc3545',
    'infoColor': '#17a2b8'
}

dark_theme = {
    'dark': True,
    'detail': '#007439',
    'primary': '#00EA64',
    'secondary': '#6E6E6E',
    'backgroundColor': '#1e1e1e',
    'textColor': '#ffffff',
    'componentBackgroundColor': '#2d2d2d',
    'borderColor': '#404040',
    'disabledColor': '#4a4a4a',
    'disabledTextColor': '#999999',
    'successColor': '#28a745',
    'warningColor': '#ffc107',
    'dangerColor': '#dc3545',
    'infoColor': '#17a2b8'
}

def log_callback(func):
    """Decorator to log callback information"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        callback_id = func.__name__
        
        # Log callback start
        logger.info(f"Callback triggered: {callback_id}")
        logger.info(f"Input arguments: {args}")
        logger.info(f"Input keyword arguments: {kwargs}")
        
        try:
            # Execute the callback
            result = func(*args, **kwargs)
            
            # Log callback completion
            execution_time = time.time() - start_time
            logger.info(f"Callback completed: {callback_id}")
            logger.info(f"Execution time: {execution_time:.2f} seconds")
            logger.info(f"Output: {result}")
            
            return result
        except Exception as e:
            # Log any errors
            logger.error(f"Callback error in {callback_id}: {str(e)}")
            raise
    
    return wrapper

# Pattern 1: Container Pattern - Always have a container output that exists
app.layout = daq.DarkThemeProvider(
    theme=dark_theme,  # Start with dark theme
    children=[
        # Theme Toggle Container
        html.Div([
            html.H3("Theme Settings"),
            daq.ToggleSwitch(
                id='theme-toggle',
                value=True,  # Default to dark theme
                label='Dark Theme',
                labelPosition='top',
                color='#00EA64',
                className='dark-theme-control',
                style={
                    'backgroundColor': 'transparent',  # Let the theme handle background
                    'color': 'var(--text-color)',  # Use theme variable
                }
            ),
        ], style={
            'padding': '20px', 
            'marginBottom': '20px',
            'backgroundColor': 'var(--component-background-color)',  # Use theme variable
            'color': 'var(--text-color)',  # Use theme variable
            'borderRadius': '8px',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
        }),
        
        # Main Content Container with theme-aware styling
        html.Div(id='main-content', children=[
            html.H1("Handling Non-Existent Outputs", style={'color': 'var(--text-color)'}),
            
            # AG Grid Section - NEW
            html.Div([
                html.H3("AG Grid with Proper Filtering", style={'color': 'var(--text-color)'}),
                html.P("This grid demonstrates proper filtering that doesn't cause the search bar to lose focus:", 
                       style={'color': 'var(--text-color)', 'marginBottom': '10px'}),
                
                # Search input
                dcc.Input(
                    id='grid-search-input',
                    type='text',
                    placeholder='Search in all columns...',
                    style={
                        'width': '100%',
                        'padding': '8px',
                        'marginBottom': '10px',
                        'border': '1px solid var(--border-color)',
                        'borderRadius': '4px',
                        'backgroundColor': 'var(--component-background-color)',
                        'color': 'var(--text-color)'
                    }
                ),
                
                # AG Grid - Only update rowData, not the entire component
                dag.AgGrid(
                    id='data-grid',
                    columnDefs=[
                        {"field": "id", "headerName": "ID", "width": 80, "sortable": True, "filter": True},
                        {"field": "name", "headerName": "Name", "width": 150, "sortable": True, "filter": True},
                        {"field": "age", "headerName": "Age", "width": 100, "sortable": True, "filter": True},
                        {"field": "department", "headerName": "Department", "width": 150, "sortable": True, "filter": True},
                        {"field": "salary", "headerName": "Salary", "width": 120, "sortable": True, "filter": True, 
                         "valueFormatter": {"function": "d3.format('$,.0f')"}}
                    ],
                    rowData=sample_data,
                    dashGridOptions={
                        "rowSelection": "single",
                        "animateRows": True,
                        "domLayout": "autoHeight"
                    },
                    style={"height": "400px", "width": "100%"}
                ),
                
                # Info display
                html.Div(id='grid-info', style={'color': 'var(--text-color)', 'marginTop': '10px'})
            ], style={
                'marginBottom': '20px',
                'padding': '15px',
                'backgroundColor': 'var(--component-background-color)',
                'borderRadius': '8px',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
            }),
            
            # Pattern 1: Container Pattern
            html.Div([
                html.H3("Pattern 1: Container Pattern", style={'color': 'var(--text-color)'}),
                dcc.Dropdown(
                    id='dropdown-1',
                    options=[{'label': f'Option {i}', 'value': i} for i in range(1, 4)],
                    value=None,
                    style={
                        'backgroundColor': 'var(--component-background-color)',
                        'color': 'var(--text-color)'
                    }
                ),
                html.Div(id='container-1', style={'color': 'var(--text-color)'})
            ], style={
                'marginBottom': '20px',
                'padding': '15px',
                'backgroundColor': 'var(--component-background-color)',
                'borderRadius': '8px',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
            }),
            
            # Pattern 2: Dynamic Output IDs
            html.Div([
                html.H3("Pattern 2: Dynamic Output IDs", style={'color': 'var(--text-color)'}),
                dcc.Dropdown(
                    id='dropdown-2',
                    options=[{'label': f'Create Output {i}', 'value': i} for i in range(1, 4)],
                    value=None,
                    style={
                        'backgroundColor': 'var(--component-background-color)',
                        'color': 'var(--text-color)'
                    }
                ),
                html.Div(id='container-2', style={'color': 'var(--text-color)'})
            ], style={
                'marginBottom': '20px',
                'padding': '15px',
                'backgroundColor': 'var(--component-background-color)',
                'borderRadius': '8px',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
            }),
            
            # Pattern 3: Pattern Matching
            html.Div([
                html.H3("Pattern 3: Pattern Matching", style={'color': 'var(--text-color)'}),
                html.Button(
                    "Add Component",
                    id='add-component',
                    n_clicks=0,
                    style={
                        'backgroundColor': 'var(--primary)',
                        'color': 'var(--text-color)',
                        'border': 'none',
                        'padding': '8px 16px',
                        'borderRadius': '4px',
                        'cursor': 'pointer'
                    }
                ),
                html.Div(id='pattern-container', style={'color': 'var(--text-color)'})
            ], style={
                'padding': '15px',
                'backgroundColor': 'var(--component-background-color)',
                'borderRadius': '8px',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
            })
        ])
    ]
)

# AG Grid filtering callback - CRITICAL: Only update rowData, not the entire component
@app.callback(
    Output('data-grid', 'rowData'),
    Input('grid-search-input', 'value'),
    prevent_initial_call=True
)
@log_callback
def filter_grid_data(search_value):
    if not search_value or search_value.strip() == '':
        return sample_data
    
    search_lower = search_value.lower().strip()
    filtered_data = []
    
    for row in sample_data:
        # Search across all string fields
        if (search_lower in str(row['name']).lower() or
            search_lower in str(row['department']).lower() or
            search_lower in str(row['age']).lower() or
            search_lower in str(row['salary']).lower() or
            search_lower in str(row['id']).lower()):
            filtered_data.append(row)
    
    return filtered_data

# Grid info callback
@app.callback(
    Output('grid-info', 'children'),
    Input('data-grid', 'rowData'),
    Input('grid-search-input', 'value')
)
@log_callback
def update_grid_info(row_data, search_value):
    if not row_data:
        return "No data to display"
    
    total_records = len(sample_data)
    filtered_records = len(row_data)
    
    if search_value and search_value.strip():
        return f"Showing {filtered_records} of {total_records} records (filtered by '{search_value}')"
    else:
        return f"Showing all {total_records} records"

# Update the toggle style callback to handle both states with higher priority
@app.callback(
    [Output('theme-toggle', 'style', allow_duplicate=True),  # Allow duplicate to override
     Output('theme-toggle', 'theme', allow_duplicate=True)],  # Allow duplicate to override
    Input('theme-toggle', 'value'),
    prevent_initial_call=True  # Prevent initial call to avoid conflicts
)
@log_callback
def update_toggle_style(is_dark):
    # Force specific styles with !important equivalent
    style = {
        'backgroundColor': 'transparent !important',
        'color': 'var(--text-color) !important',
        'border': 'none !important',
        'padding': '10px !important',
        'margin': '10px !important',
        '--switch-track-color': '#4a4a4a !important',  # Force track color
        '--switch-track-color-checked': '#007439 !important',  # Force track color when ON
        '--switch-handle-color': '#ffffff !important',  # Force handle color
        '--switch-handle-color-checked': '#00EA64 !important',  # Force handle color when ON
    }
    
    # Force theme properties
    theme = {
        'dark': is_dark,
        'detail': '#007439 !important',
        'primary': '#00EA64 !important',
        'secondary': '#6E6E6E !important',
        'toggleBackground': '#4a4a4a !important',
        'toggleColor': '#007439 !important',
        'handleColor': '#ffffff !important',
        'handleBorderColor': '#00EA64 !important',
    }
    
    return style, theme

# Add a separate callback for the main content theme
@app.callback(
    Output('main-content', 'style'),
    Input('theme-toggle', 'value'),
    prevent_initial_call=True
)
@log_callback
def update_main_theme(is_dark):
    theme = dark_theme if is_dark else light_theme
    return {
        'backgroundColor': theme['backgroundColor'],
        'color': theme['textColor'],
        'padding': '20px',
        'borderRadius': '5px',
        'marginBottom': '20px'
    }

# Update component styles based on theme
@app.callback(
    [Output('dropdown-1', 'style'),
     Output('dropdown-2', 'style'),
     Output('grid-search-input', 'style')],
    Input('theme-toggle', 'value')
)
@log_callback
def update_component_styles(is_dark):
    theme = dark_theme if is_dark else light_theme
    dropdown_style = {
        'backgroundColor': theme['componentBackgroundColor'],
        'color': theme['textColor']
    }
    search_style = {
        'width': '100%',
        'padding': '8px',
        'marginBottom': '10px',
        'border': f'1px solid {theme["borderColor"]}',
        'borderRadius': '4px',
        'backgroundColor': theme['componentBackgroundColor'],
        'color': theme['textColor']
    }
    return dropdown_style, dropdown_style, search_style

# Pattern 1: Container Pattern
@app.callback(
    Output('container-1', 'children'),  # Container always exists
    Input('dropdown-1', 'value')
)
@log_callback
def update_container(value):
    if value is None:
        return "Select an option"
    
    # Create the output inside the container
    return html.Div([
        html.H4(f"Selected: {value}"),
        html.Div(id=f'dynamic-output-{value}')  # This output is created dynamically
    ])

# Pattern 2: Dynamic Output IDs
@app.callback(
    Output('container-2', 'children'),
    Input('dropdown-2', 'value')
)
@log_callback
def create_dynamic_output(value):
    if value is None:
        return "Select to create output"
    
    # Create a new output with a dynamic ID
    return html.Div([
        html.H4(f"Dynamic Output {value}"),
        html.Button(
            f"Update Output {value}",
            id={'type': 'dynamic-button', 'index': value},
            n_clicks=0
        ),
        html.Div(
            "Not clicked",
            id={'type': 'dynamic-output', 'index': value}
        )
    ])

# Pattern 3: Pattern Matching
@app.callback(
    Output('pattern-container', 'children'),
    Input('add-component', 'n_clicks'),
    State('pattern-container', 'children')
)
@log_callback
def add_pattern_component(n_clicks, existing_children):
    if n_clicks == 0:
        return []
    
    new_component = html.Div([
        html.Button(
            f"Component {n_clicks}",
            id={'type': 'pattern-button', 'index': n_clicks},
            n_clicks=0
        ),
        html.Div(
            "Not clicked",
            id={'type': 'pattern-output', 'index': n_clicks}
        )
    ])
    
    return existing_children + [new_component] if existing_children else [new_component]

# Callback for Pattern 2 (Dynamic Outputs)
@app.callback(
    Output({'type': 'dynamic-output', 'index': MATCH}, 'children'),
    Input({'type': 'dynamic-button', 'index': MATCH}, 'n_clicks'),
    prevent_initial_call=True
)
@log_callback
def update_dynamic_output(n_clicks):
    if n_clicks is None:
        return no_update
    return f"Clicked {n_clicks} times"

# Callback for Pattern 3 (Pattern Matching)
@app.callback(
    Output({'type': 'pattern-output', 'index': MATCH}, 'children'),
    Input({'type': 'pattern-button', 'index': MATCH}, 'n_clicks'),
    prevent_initial_call=True
)
@log_callback
def update_pattern_output(n_clicks):
    if n_clicks is None:
        return no_update
    return f"Clicked {n_clicks} times"

if __name__ == '__main__':
    app.run_server(debug=True) 