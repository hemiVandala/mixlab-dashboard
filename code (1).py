import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sqlite3
import datetime
import time
import random
import json

# --- Page Configuration ---
st.set_page_config(
    page_title="MixLab - E-Liquid Recipe Developer",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Dark Theme UI Customization ---
st.markdown("""
<style>
    .reportview-container {
        background: #0E1117;
    }
    .sidebar .sidebar-content {
        background: #0E1117;
    }
    .stButton>button {
        color: #FFFFFF;
        background-color: #262730;
        border-radius: 8px;
        border: 1px solid #262730;
    }
    .stButton>button:hover {
        border: 1px solid #00A36C;
        color: #00A36C;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #1E1E1E;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #00A36C;
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


# --- Database Setup ---
def init_db():
    conn = sqlite3.connect('mixlab.db')
    c = conn.cursor()
    # Stash Table: id, name, brand, category (for AI analysis)
    c.execute('''
        CREATE TABLE IF NOT EXISTS flavor_stash (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            brand TEXT,
            category TEXT
        )
    ''')
    # Recipes Table: id, name, steep_days, created_at, steep_end_date, status
    c.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            notes TEXT,
            steep_days INTEGER DEFAULT 7,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            steep_end_date TIMESTAMP,
            status TEXT DEFAULT 'Steeping'
        )
    ''')
    # Recipe Flavors Table: Links flavors and percentages to a recipe
    c.execute('''
        CREATE TABLE IF NOT EXISTS recipe_flavors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER,
            flavor_name TEXT,
            percentage REAL,
            FOREIGN KEY (recipe_id) REFERENCES recipes (id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database on first run
init_db()

# --- Database Helper Functions ---
def run_query(query, params=(), fetch=None):
    conn = sqlite3.connect('mixlab.db')
    c = conn.cursor()
    c.execute(query, params)
    if fetch == "one":
        result = c.fetchone()
    elif fetch == "all":
        result = c.fetchall()
    else:
        result = None
    conn.commit()
    conn.close()
    return result

# --- VapeSim AI Mock Logic ---
FLAVOR_PROPERTIES = {
    'Fruit': {'note': 'Top', 'type': 'Primary'},
    'Sweetener': {'note': 'Accent', 'type': 'Enhancer'},
    'Cream': {'note': 'Base', 'type': 'Mouthfeel'},
    'Custard': {'note': 'Base', 'type': 'Mouthfeel'},
    'Bakery': {'note': 'Mid', 'type': 'Primary'},
    'Menthol': {'note': 'Accent', 'type': 'Effect'},
    'Tobacco': {'note': 'Base', 'type': 'Primary'},
    'Beverage': {'note': 'Mid', 'type': 'Primary'},
    'Other': {'note': 'Mid', 'type': 'Misc'}
}

def get_flavor_category(flavor_name):
    stash = run_query("SELECT name, category FROM flavor_stash", fetch="all")
    stash_map = {name.lower(): category for name, category in stash}
    return stash_map.get(flavor_name.lower(), 'Other')

def vapesim_analyze(recipe_flavors):
    """Mocks an AI analysis of a recipe."""
    analysis = {
        "summary": "", "balance": {"Top": 0, "Mid": 0, "Base": 0, "Accent": 0},
        "sweetness": 0, "density": 0, "steep_curve": [], "warnings": []
    }
    total_percentage = sum(f['percentage'] for f in recipe_flavors)
    
    # Generate Summary & Warnings
    summary_parts = []
    cream_pct = 0
    fruit_pct = 0
    
    for flavor in recipe_flavors:
        category = get_flavor_category(flavor['flavor_name'])
        props = FLAVOR_PROPERTIES.get(category, FLAVOR_PROPERTIES['Other'])
        analysis['balance'][props['note']] += flavor['percentage']
        
        if category == 'Cream' or category == 'Custard':
            cream_pct += flavor['percentage']
        if category == 'Fruit':
            fruit_pct += flavor['percentage']
        if category == 'Sweetener':
            analysis['sweetness'] += flavor['percentage'] * 5 # Sweeteners are potent
        
        if flavor['percentage'] > 8:
            analysis['warnings'].append(f"High concentration of {flavor['flavor_name']} ({flavor['percentage']}%) may lead to oversaturation or muting.")
    
    if cream_pct > 10:
        summary_parts.append("This is a very cream-heavy profile, suggesting a thick, dense vape.")
        analysis['warnings'].append("High total cream percentage may require a longer steep.")
    if fruit_pct > cream_pct:
        summary_parts.append("The profile is fruit-dominant, likely bright and sharp.")
    if "Menthol" in [get_flavor_category(f['flavor_name']) for f in recipe_flavors] and "Cream" in [get_flavor_category(f['flavor_name']) for f in recipe_flavors]:
         analysis['warnings'].append("Potential clash: Menthol and Cream can sometimes curdle or separate perceptions.")

    if not summary_parts:
        summary_parts.append("A balanced mix with potential for complexity.")

    analysis['summary'] = " ".join(summary_parts)
    
    # Calculate other metrics
    analysis['density'] = min(100, (cream_pct * 5) + (total_percentage * 2))
    analysis['sweetness'] = min(100, analysis['sweetness'] + fruit_pct)
    
    # Steep Curve Projection
    analysis['steep_curve'] = [
        {'Day': 1, 'Flavor': 30 + fruit_pct},
        {'Day': 7, 'Flavor': 50 + (total_percentage*1.5)},
        {'Day': 14, 'Flavor': 75 + cream_pct},
        {'Day': 30, 'Flavor': 95}
    ]

    return analysis


# --- UI Rendering ---

# --- Sidebar ---
with st.sidebar:
    st.title("🧪 MixLab")
    st.markdown("---")

    # Module 6: Quick Mix Assistant
    st.header("💡 Quick Mix Assistant")
    profile_input = st.text_input("Describe your desired flavor profile", placeholder="e.g., Creamy strawberry shortcake")
    if st.button("Generate Recipe Suggestion"):
        with st.spinner("Asking the AI chef..."):
            time.sleep(1) # Simulate AI thinking
            stash_df = pd.DataFrame(run_query("SELECT name, category FROM flavor_stash", fetch="all"), columns=['name', 'category'])
            if stash_df.empty:
                st.warning("Your flavor stash is empty! Add flavors to get suggestions.")
            else:
                st.subheader("AI Suggested Recipe:")
                keywords = profile_input.lower().split()
                
                # Simple keyword matching logic
                suggested_flavors = []
                if any(k in keywords for k in ['strawberry', 'berry', 'fruit']):
                    fruit_flavors = stash_df[stash_df['category'] == 'Fruit']
                    if not fruit_flavors.empty:
                        suggested_flavors.append({'name': fruit_flavors.sample(1).iloc[0]['name'], 'pct': round(random.uniform(2.5, 5.0), 1)})

                if any(k in keywords for k in ['creamy', 'custard', 'milk']):
                    cream_flavors = stash_df[stash_df['category'].isin(['Cream', 'Custard'])]
                    if not cream_flavors.empty:
                        suggested_flavors.append({'name': cream_flavors.sample(1).iloc[0]['name'], 'pct': round(random.uniform(3.0, 6.0), 1)})

                if any(k in keywords for k in ['cake', 'bakery', 'biscuit', 'shortcake']):
                    bakery_flavors = stash_df[stash_df['category'] == 'Bakery']
                    if not bakery_flavors.empty:
                        suggested_flavors.append({'name': bakery_flavors.sample(1).iloc[0]['name'], 'pct': round(random.uniform(1.0, 3.0), 1)})

                if not suggested_flavors:
                    st.error("Couldn't find matching flavors in your stash for that profile.")
                else:
                    for flav in suggested_flavors:
                        st.write(f"- **{flav['name']}**: {flav['pct']}%")
                    st.info(f"**Suggested Steep Time:** {random.choice([7, 14, 21])} days")


# --- Main Content Tabs ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📋 Recipe Manager", "🫙 Flavor Stash", "⏳ Steep Tracker",
    "🤖 VapeSim AI", "🔥 Synergy Matrix", "↔️ Recipe Diff Tool"
])


# --- Module 1: Recipe Input & Manager ---
with tab1:
    st.header("📋 Recipe Manager")
    
    # Fetch all recipes for display
    recipes_list = run_query("SELECT id, name, steep_days, status FROM recipes ORDER BY created_at DESC", fetch="all")
    recipes_df = pd.DataFrame(recipes_list, columns=["ID", "Name", "Steep Days", "Status"])

    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("All Recipes")
        if not recipes_df.empty:
            st.dataframe(recipes_df, use_container_width=True, hide_index=True)
        else:
            st.info("No recipes yet. Add one to get started!")

        st.subheader("Recipe Actions")
        if not recipes_df.empty:
            selected_recipe_id = st.selectbox("Select Recipe for Actions", options=recipes_df['ID'], format_func=lambda x: recipes_df[recipes_df['ID'] == x]['Name'].iloc[0])
            
            action_cols = st.columns(4)
            
            # Delete
            if action_cols[0].button("🗑️ Delete"):
                run_query("DELETE FROM recipes WHERE id=?", (selected_recipe_id,))
                st.success(f"Recipe ID {selected_recipe_id} deleted.")
                st.rerun()

            # Duplicate
            if action_cols[1].button("👯 Duplicate"):
                orig_recipe = run_query("SELECT name, notes, steep_days FROM recipes WHERE id=?", (selected_recipe_id,), fetch="one")
                orig_flavors = run_query("SELECT flavor_name, percentage FROM recipe_flavors WHERE recipe_id=?", (selected_recipe_id,), fetch="all")
                
                new_name = f"{orig_recipe[0]} (Copy)"
                run_query("INSERT INTO recipes (name, notes, steep_days, status) VALUES (?, ?, ?, ?)", (new_name, orig_recipe[1], orig_recipe[2], 'Steeping'))
                new_recipe_id = run_query("SELECT last_insert_rowid()", fetch="one")[0]
                
                for flav_name, pct in orig_flavors:
                    run_query("INSERT INTO recipe_flavors (recipe_id, flavor_name, percentage) VALUES (?, ?, ?)", (new_recipe_id, flav_name, pct))
                
                st.success(f"Duplicated '{orig_recipe[0]}' as '{new_name}'.")
                st.rerun()

            # Export to Text
            if action_cols[2].button("📋 Export to Text"):
                recipe_info = run_query("SELECT name, notes FROM recipes WHERE id=?", (selected_recipe_id,), fetch="one")
                flavor_info = run_query("SELECT flavor_name, percentage FROM recipe_flavors WHERE recipe_id=?", (selected_recipe_id,), fetch="all")
                
                export_str = f"--- {recipe_info[0]} ---\n"
                if recipe_info[1]:
                    export_str += f"Notes: {recipe_info[1]}\n\n"
                for name, pct in flavor_info:
                    export_str += f"- {name}: {pct}%\n"
                
                st.code(export_str)

    with col2:
        st.subheader("Create or Edit Recipe")
        
        # Fetch flavors for the dropdown
        stash = run_query("SELECT name FROM flavor_stash ORDER BY name", fetch="all")
        flavor_options = [s[0] for s in stash] if stash else []

        with st.form("recipe_form"):
            recipe_id_to_edit = st.selectbox("Edit Existing Recipe (Optional)", ["New Recipe"] + list(recipes_df['ID']), format_func=lambda x: "New Recipe" if x == "New Recipe" else recipes_df[recipes_df['ID'] == x]['Name'].iloc[0])

            if recipe_id_to_edit != "New Recipe":
                # Load existing recipe data
                recipe_data = run_query("SELECT name, notes, steep_days FROM recipes WHERE id=?", (recipe_id_to_edit,), fetch="one")
                flavor_data = run_query("SELECT flavor_name, percentage FROM recipe_flavors WHERE recipe_id=?", (recipe_id_to_edit,), fetch="all")
                
                recipe_name = st.text_input("Recipe Name", value=recipe_data[0])
                recipe_notes = st.text_area("Notes", value=recipe_data[1])
                steep_days = st.number_input("Steep Time (days)", min_value=0, value=recipe_data[2])
                
                if 'flavors' not in st.session_state or st.session_state.get('editing_id') != recipe_id_to_edit:
                    st.session_state.flavors = [{'name': f[0], 'percentage': f[1]} for f in flavor_data]
                    st.session_state.editing_id = recipe_id_to_edit
            else:
                # New recipe form
                recipe_name = st.text_input("Recipe Name", placeholder="My Awesome Creation")
                recipe_notes = st.text_area("Notes", placeholder="Tastes like...")
                steep_days = st.number_input("Steep Time (days)", min_value=0, value=7)
                if 'flavors' not in st.session_state or st.session_state.get('editing_id') != 'new':
                    st.session_state.flavors = []
                    st.session_state.editing_id = 'new'

            st.markdown("---")
            st.write("**Flavors**")

            # Dynamic flavor inputs
            for i, flavor in enumerate(st.session_state.flavors):
                cols = st.columns([4, 2, 1])
                st.session_state.flavors[i]['name'] = cols[0].selectbox(f"Flavor {i+1}", flavor_options, index=flavor_options.index(flavor['name']) if flavor['name'] in flavor_options else 0, key=f"name_{i}")
                st.session_state.flavors[i]['percentage'] = cols[1].number_input("%", min_value=0.0, max_value=25.0, value=flavor['percentage'], step=0.1, key=f"pct_{i}", label_visibility="collapsed")
                if cols[2].button("❌", key=f"del_{i}"):
                    st.session_state.flavors.pop(i)
                    st.rerun()

            if st.button("Add Flavor"):
                if flavor_options:
                    st.session_state.flavors.append({'name': flavor_options[0], 'percentage': 1.0})
                else:
                    st.warning("Please add flavors to your stash first!")
                st.rerun()

            submitted = st.form_submit_button("💾 Save Recipe")

            if submitted:
                if not recipe_name or not st.session_state.flavors:
                    st.error("Recipe name and at least one flavor are required.")
                else:
                    steep_end_date = (datetime.datetime.now() + datetime.timedelta(days=steep_days)).isoformat()
                    if recipe_id_to_edit == "New Recipe":
                        run_query("INSERT INTO recipes (name, notes, steep_days, steep_end_date) VALUES (?, ?, ?, ?)", (recipe_name, recipe_notes, steep_days, steep_end_date))
                        new_recipe_id = run_query("SELECT last_insert_rowid()", fetch="one")[0]
                        for f in st.session_state.flavors:
                           run_query("INSERT INTO recipe_flavors (recipe_id, flavor_name, percentage) VALUES (?, ?, ?)", (new_recipe_id, f['name'], f['percentage']))
                        st.success(f"Recipe '{recipe_name}' saved!")
                    else: # Updating
                        run_query("UPDATE recipes SET name=?, notes=?, steep_days=?, steep_end_date=? WHERE id=?", (recipe_name, recipe_notes, steep_days, steep_end_date, recipe_id_to_edit))
                        # Clear old flavors and add new ones
                        run_query("DELETE FROM recipe_flavors WHERE recipe_id=?", (recipe_id_to_edit,))
                        for f in st.session_state.flavors:
                           run_query("INSERT INTO recipe_flavors (recipe_id, flavor_name, percentage) VALUES (?, ?, ?)", (recipe_id_to_edit, f['name'], f['percentage']))
                        st.success(f"Recipe '{recipe_name}' updated!")
                    
                    st.session_state.flavors = []
                    st.session_state.editing_id = None
                    st.rerun()

# --- Module 2: Flavor Stash Editor ---
with tab2:
    st.header("🫙 Flavor Stash")
    st.info("Manage your personal inventory of flavor concentrates here. This list powers the autocomplete in the recipe manager and AI analysis.")
    
    # Pre-defined categories for consistency
    CATEGORIES = ['Fruit', 'Cream', 'Custard', 'Bakery', 'Menthol', 'Sweetener', 'Tobacco', 'Beverage', 'Other']

    # Load stash into a DataFrame
    stash_data = run_query("SELECT id, name, brand, category FROM flavor_stash ORDER BY name", fetch="all")
    stash_df = pd.DataFrame(stash_data, columns=['id', 'Name', 'Brand', 'Category'])

    # Use st.data_editor for a spreadsheet-like experience
    edited_df = st.data_editor(
        stash_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "id": None, # Hide the ID column
            "Name": st.column_config.TextColumn("Flavor Name", required=True),
            "Brand": st.column_config.TextColumn("Brand (e.g., TFA, CAP)"),
            "Category": st.column_config.SelectboxColumn("Category", options=CATEGORIES, required=True)
        },
        hide_index=True
    )

    if st.button("💾 Save Stash Changes"):
        # Simple diffing logic to update the database
        try:
            # Drop rows that were deleted in the UI
            deleted_ids = set(stash_df['id']) - set(edited_df[edited_df['id'].notna()]['id'])
            for del_id in deleted_ids:
                run_query("DELETE FROM flavor_stash WHERE id=?", (int(del_id),))

            # Iterate through the edited dataframe to add/update
            for _, row in edited_df.iterrows():
                if pd.notna(row['id']): # Update existing row
                    run_query("UPDATE flavor_stash SET name=?, brand=?, category=? WHERE id=?", (row['Name'], row['Brand'], row['Category'], int(row['id'])))
                else: # Add new row
                    run_query("INSERT INTO flavor_stash (name, brand, category) VALUES (?, ?, ?)", (row['Name'], row['Brand'], row['Category']))
            
            st.success("Flavor stash updated successfully!")
            time.sleep(1) # Give user time to see success message
            st.rerun()

        except Exception as e:
            st.error(f"An error occurred: {e}. A common issue is trying to add a flavor name that already exists.")

# --- Module 3: Steep Timer Tracker ---
with tab3:
    st.header("⏳ Steep Timer Tracker")
    st.info("Track the steeping progress of your recipes.")
    
    # Fetch recipes with steep times
    steeping_recipes = run_query("SELECT id, name, steep_days, steep_end_date, status FROM recipes WHERE steep_days > 0 ORDER BY steep_end_date", fetch="all")
    
    if not steeping_recipes:
        st.warning("No recipes are currently steeping. Create a recipe with a steep time greater than 0.")
    else:
        for r_id, name, steep_days, end_date_str, status in steeping_recipes:
            with st.expander(f"**{name}** - Status: **{status}**"):
                end_date = datetime.datetime.fromisoformat(end_date_str)
                now = datetime.datetime.now()
                
                if now >= end_date:
                    st.success("🎉 This recipe is ready!")
                    if status != "Ready":
                        run_query("UPDATE recipes SET status='Ready' WHERE id=?", (r_id,))
                else:
                    time_left = end_date - now
                    days_left = time_left.days
                    hours_left, remainder = divmod(time_left.seconds, 3600)
                    minutes_left, _ = divmod(remainder, 60)
                    
                    st.write(f"**Steep End Date:** {end_date.strftime('%Y-%m-%d %H:%M')}")
                    st.write(f"**Time Remaining:** {days_left} days, {hours_left} hours, {minutes_left} minutes")

                    # Visual Countdown
                    total_duration_seconds = steep_days * 24 * 3600
                    elapsed_seconds = total_duration_seconds - time_left.total_seconds()
                    progress = min(1.0, elapsed_seconds / total_duration_seconds)
                    st.progress(progress)

                # Status update
                new_status = st.radio("Update Status", ["Steeping", "Ready"], index=0 if status == "Steeping" else 1, key=f"status_{r_id}", horizontal=True)
                if new_status != status:
                    run_query("UPDATE recipes SET status=? WHERE id=?", (new_status, r_id))
                    st.rerun()

# --- Module 4: VapeSim AI Integration ---
with tab4:
    st.header("🤖 VapeSim AI Analysis")
    st.info("Select a saved recipe to simulate its flavor profile, balance, and other characteristics.")

    recipes_list = run_query("SELECT id, name FROM recipes ORDER BY name", fetch="all")
    if not recipes_list:
        st.warning("Create a recipe first to use the simulator.")
    else:
        recipe_options = {name: r_id for r_id, name in recipes_list}
        selected_recipe_name = st.selectbox("Choose a recipe to analyze", options=recipe_options.keys())
        
        if selected_recipe_name:
            recipe_id = recipe_options[selected_recipe_name]
            flavors_list = run_query("SELECT flavor_name, percentage FROM recipe_flavors WHERE recipe_id=?", (recipe_id,), fetch="all")
            flavors_for_ai = [{'flavor_name': f[0], 'percentage': f[1]} for f in flavors_list]
            
            with st.spinner("Simulating flavor molecules..."):
                time.sleep(1) # Simulate processing
                analysis_results = vapesim_analyze(flavors_for_ai)
            
            st.subheader("VapeSim™ Report")
            
            # Display warnings first
            if analysis_results['warnings']:
                for warning in analysis_results['warnings']:
                    st.warning(f"**Warning:** {warning}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Predicted Sweetness", f"{analysis_results['sweetness']:.0f}/100")
                st.metric("Predicted Density/Mouthfeel", f"{analysis_results['density']:.0f}/100")
                
                st.subheader("Flavor Profile Summary")
                st.write(analysis_results['summary'])
                
            with col2:
                # Balance Chart
                st.subheader("Flavor Balance (Top/Mid/Base/Accent)")
                balance_df = pd.DataFrame(list(analysis_results['balance'].items()), columns=['Note', 'Percentage'])
                fig = go.Figure(go.Bar(
                    x=balance_df['Percentage'],
                    y=balance_df['Note'],
                    orientation='h',
                    marker_color=['#76D7C4', '#F7DC6F', '#E59866', '#D7BDE2']
                ))
                fig.update_layout(title="Profile Balance by Note", xaxis_title="Total Percentage (%)", yaxis_title="Note", template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)

            # Steep Curve Projection
            st.subheader("Steep Curve Projection")
            steep_df = pd.DataFrame(analysis_results['steep_curve'])
            steep_fig = go.Figure(go.Scatter(
                x=steep_df['Day'], y=steep_df['Flavor'], mode='lines+markers',
                line=dict(color='#00A36C', width=3)
            ))
            steep_fig.update_layout(title="Flavor Meld Over Time", xaxis_title="Days Steeping", yaxis_title="Flavor Profile Maturity (%)", yaxis_range=[0,100], template="plotly_dark")
            st.plotly_chart(steep_fig, use_container_width=True)


# --- Module 5: Flavor Synergy Heatmap ---
with tab5:
    st.header("🔥 Flavor Synergy Heatmap")
    st.info("Visualize which flavors in your stash might work well together. The 'synergy score' is a mock calculation based on classic pairing categories.")

    stash = run_query("SELECT name, category FROM flavor_stash", fetch="all")
    if len(stash) < 2:
        st.warning("You need at least two flavors in your stash to generate a synergy matrix.")
    else:
        flavor_names = [f[0] for f in stash]
        flavor_categories = {f[0]: f[1] for f in stash}

        # Mock synergy logic
        def get_synergy(cat1, cat2):
            if cat1 == cat2: return 0.3 # e.g., two fruits
            if (cat1 in ['Fruit'] and cat2 in ['Cream', 'Custard']) or \
               (cat2 in ['Fruit'] and cat1 in ['Cream', 'Custard']): return 0.9
            if (cat1 in ['Bakery'] and cat2 in ['Fruit', 'Cream', 'Custard']) or \
               (cat2 in ['Bakery'] and cat1 in ['Fruit', 'Cream', 'Custard']): return 0.8
            if (cat1 in ['Tobacco'] and cat2 in ['Cream', 'Custard', 'Bakery']) or \
               (cat2 in ['Tobacco'] and cat1 in ['Cream', 'Custard', 'Bakery']): return 0.7
            if (cat1 in ['Menthol'] and cat2 in ['Fruit']) or \
               (cat2 in ['Menthol'] and cat1 in ['Fruit']): return 0.6
            if (cat1 in ['Sweetener']) or (cat2 in ['Sweetener']): return 0.5
            return 0.1 # Low but not zero synergy

        # Create synergy matrix
        synergy_data = []
        high_synergy_pairs = []
        for f1 in flavor_names:
            row = []
            for f2 in flavor_names:
                if f1 == f2:
                    score = 1.0
                else:
                    score = get_synergy(flavor_categories[f1], flavor_categories[f2])
                    if score > 0.75 and {f1, f2} not in [set(p) for p in high_synergy_pairs]:
                         high_synergy_pairs.append((f1, f2, score))
                row.append(score)
            synergy_data.append(row)

        col1, col2 = st.columns([3, 1])

        with col1:
            st.subheader("Synergy Matrix")
            fig = go.Figure(data=go.Heatmap(
                z=synergy_data,
                x=flavor_names,
                y=flavor_names,
                colorscale='Greens',
                hoverongaps=False))
            fig.update_layout(title='Flavor Pairing Potential', template='plotly_dark')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Top Pairings")
            high_synergy_pairs.sort(key=lambda x: x[2], reverse=True)
            if not high_synergy_pairs:
                st.info("No high-synergy pairs found based on current logic.")
            else:
                for f1, f2, score in high_synergy_pairs[:10]: # Show top 10
                    st.success(f"**{f1}** + **{f2}**")


# --- Module 7: Recipe Diff Tool ---
with tab6:
    st.header("↔️ Recipe Diff Tool")
    st.info("Compare two recipes side-by-side to see differences in ingredients and percentages.")

    recipes_list = run_query("SELECT id, name FROM recipes ORDER BY name", fetch="all")
    if len(recipes_list) < 2:
        st.warning("You need at least two saved recipes to use the comparison tool.")
    else:
        recipe_options_df = pd.DataFrame(recipes_list, columns=['id', 'name'])
        
        col1, col2 = st.columns(2)
        with col1:
            recipe_a_name = st.selectbox("Select Recipe A", recipe_options_df['name'], key="recipe_a")
        with col2:
            recipe_b_name = st.selectbox("Select Recipe B", recipe_options_df['name'], key="recipe_b", index=1 if len(recipe_options_df) > 1 else 0)

        if recipe_a_name and recipe_b_name:
            # Fetch data for Recipe A
            id_a = recipe_options_df[recipe_options_df['name'] == recipe_a_name]['id'].iloc[0]
            flavors_a = run_query("SELECT flavor_name, percentage FROM recipe_flavors WHERE recipe_id=?", (int(id_a),), fetch="all")
            flavors_a_dict = {f[0]: f[1] for f in flavors_a}
            
            # Fetch data for Recipe B
            id_b = recipe_options_df[recipe_options_df['name'] == recipe_b_name]['id'].iloc[0]
            flavors_b = run_query("SELECT flavor_name, percentage FROM recipe_flavors WHERE recipe_id=?", (int(id_b),), fetch="all")
            flavors_b_dict = {f[0]: f[1] for f in flavors_b}
            
            # Get all unique flavors from both recipes
            all_flavors = sorted(list(set(flavors_a_dict.keys()) | set(flavors_b_dict.keys())))

            # Create comparison DataFrame
            diff_data = []
            for flavor in all_flavors:
                pct_a = flavors_a_dict.get(flavor, 0)
                pct_b = flavors_b_dict.get(flavor, 0)
                diff = pct_b - pct_a
                diff_data.append([flavor, pct_a, pct_b, diff])
            
            diff_df = pd.DataFrame(diff_data, columns=['Flavor', recipe_a_name, recipe_b_name, 'Difference'])

            st.subheader("Ingredient Comparison")

            def style_diff(val):
                if val > 0:
                    return f"color: #2ECC71; font-weight: bold;" # Green for increase
                elif val < 0:
                    return f"color: #E74C3C; font-weight: bold;" # Red for decrease
                return ""

            st.dataframe(
                diff_df.style.format({
                    recipe_a_name: "{:.2f}%",
                    recipe_b_name: "{:.2f}%",
                    "Difference": "{:+.2f}%"
                }).applymap(
                    style_diff, subset=['Difference']
                ),
                use_container_width=True,
                hide_index=True
            )

            # AI Profile Comparison
            st.subheader("VapeSim Profile Comparison")
            sim_a = vapesim_analyze([{'flavor_name': k, 'percentage': v} for k, v in flavors_a_dict.items()])
            sim_b = vapesim_analyze([{'flavor_name': k, 'percentage': v} for k, v in flavors_b_dict.items()])

            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**{recipe_a_name} Profile**")
                st.write(sim_a['summary'])
                if sim_a['warnings']:
                    for w in sim_a['warnings']: st.write(f"⚠️ {w}")
            
            with c2:
                st.markdown(f"**{recipe_b_name} Profile**")
                st.write(sim_b['summary'])
                if sim_b['warnings']:
                    for w in sim_b['warnings']: st.write(f"⚠️ {w}")