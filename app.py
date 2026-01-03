import streamlit as st
import google.generativeai as genai
import json

# --- CONFIGURATION ---
st.set_page_config(page_title="Personal Meal Planner", page_icon="🥑", layout="wide")

# Validates API Key
def init_gemini(api_key):
    try:
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        st.error(f"API Key Error: {e}")
        return False

# --- SIDEBAR: USER INPUTS ---
st.sidebar.title("🍳 Meal Preferences")

api_key = st.sidebar.text_input("Enter Gemini API Key", type="password", help="Get one at aistudio.google.com")

st.sidebar.subheader("Constraints")
total_meals = st.sidebar.slider("Meals to Plan", 1, 7, 3)
servings = st.sidebar.number_input("Servings per Meal", min_value=1, value=2)
complexity = st.sidebar.select_slider("Complexity", options=["Easy", "Medium", "Gourmet/Difficult"])
cook_ware = st.sidebar.multiselect("Available Cookware", ["One Pot", "Sheet Pan", "Slow Cooker", "Air Fryer", "Stove Top", "Oven"], default=["Stove Top", "Oven"])
max_ingredients = st.sidebar.radio("Ingredient Limit", ["Under 5", "Unlimited"], index=1)

st.sidebar.subheader("Dietary & Budget")
diet_type = st.sidebar.selectbox("Diet Goal", ["Balanced", "High Protein", "Vegan", "Vegetarian", "Keto", "Paleo"])
avoid_list = st.sidebar.multiselect("Ingredients to Avoid", ["Mushrooms", "Nuts", "Dairy", "Gluten", "Shellfish", "Beef", "Pork"])
cuisine = st.sidebar.selectbox("Cuisine Preference", ["No Preference", "Italian", "Mexican", "Asian", "Mediterranean", "American"])
budget_target = st.sidebar.number_input("Target Budget ($)", min_value=10, value=50, step=5)

# --- APP LOGIC ---
st.title("🥗 AI Personal Meal Planner")
st.markdown("Generates personalized recipes and shopping lists based on your specific constraints.")

if st.sidebar.button("Generate Meal Plan"):
    if not api_key:
        st.error("Please enter a valid Gemini API Key in the sidebar.")
    else:
        init_gemini(api_key)
        
        # 1. CONSTRUCT THE PROMPT
        prompt = f"""
        Act as a professional chef and nutritionist. Create a meal plan for {total_meals} dinners.
        
        Constraints:
        - Servings: {servings} people per meal.
        - Complexity: {complexity}
        - Cookware allowed: {", ".join(cook_ware)}
        - Max Ingredients: {max_ingredients}
        - Diet: {diet_type}
        - Avoid: {", ".join(avoid_list)}
        - Cuisine: {cuisine}
        - Budget Target: Keep total ingredients under ${budget_target} (estimate generic US grocery prices).
        
        Output Format:
        Return ONLY valid JSON. Do not include markdown formatting like ```json.
        Structure:
        {{
            "meals": [
                {{
                    "title": "Recipe Name",
                    "time_minutes": 30,
                    "estimated_cost": 15.00,
                    "ingredients": ["item 1", "item 2"],
                    "instructions": ["step 1", "step 2"]
                }}
            ],
            "shopping_list": {{
                "Produce": ["item", "item"],
                "Pantry": ["item"],
                "Protein": ["item"]
            }}
        }}
        """

        with st.spinner('Chef Gemini is writing your menu...'):
            try:
                # 2. CALL GEMINI
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                
                # Clean up response to ensure it's pure JSON
                clean_json = response.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(clean_json)

                # 3. DISPLAY RESULTS
                tab1, tab2 = st.tabs(["🍽️ Recipes", "🛒 Shopping List"])

                with tab1:
                    total_est_cost = sum(m.get('estimated_cost', 0) for m in data['meals'])
                    
                    # Budget Check
                    if total_est_cost > budget_target:
                        st.warning(f"Note: Estimated cost (${total_est_cost}) is slightly over your budget of ${budget_target}.")
                    else:
                        st.success(f"Plan is within budget! Est: ${total_est_cost}")

                    for meal in data['meals']:
                        with st.expander(f"**{meal['title']}** ({meal['time_minutes']} min) - Est: ${meal['estimated_cost']}"):
                            col1, col2 = st.columns([1, 2])
                            with col1:
                                st.image("[https://images.unsplash.com/photo-1498837167922-ddd27525d352?q=80&w=400&auto=format&fit=crop](https://images.unsplash.com/photo-1498837167922-ddd27525d352?q=80&w=400&auto=format&fit=crop)", caption="Suggestion")
                                st.markdown("**Ingredients:**")
                                for ing in meal['ingredients']:
                                    st.markdown(f"- {ing}")
                            with col2:
                                st.markdown("**Instructions:**")
                                for i, step in enumerate(meal['instructions'], 1):
                                    st.markdown(f"{i}. {step}")

                with tab2:
                    st.header("Shopping List")
                    for category, items in data['shopping_list'].items():
                        st.subheader(category)
                        for item in items:
                            st.checkbox(item, key=item)
            
            except json.JSONDecodeError:
                st.error("Error parsing AI response. Please try again.")
            except Exception as e:
                st.error(f"An error occurred: {e}")
