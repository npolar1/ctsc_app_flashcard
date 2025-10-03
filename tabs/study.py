import streamlit as st
import pandas as pd
from utils.database import get_snowflake_connection
import time
import random

def show_study(current_user):
    """Content of the Study tab"""
    st.header("🎴 Study Mode")
    
    if not current_user:
        st.warning("🔐 You must sign in to view the study mode.")
        return
    
    # Initialize session state for question management
    if 'question_queue' not in st.session_state:
        st.session_state.question_queue = []
    if 'current_question_index' not in st.session_state:
        st.session_state.current_question_index = 0
    if 'question_start_time' not in st.session_state:
        st.session_state.question_start_time = None
    if 'answer_submitted' not in st.session_state:
        st.session_state.answer_submitted = False
    if 'selected_module' not in st.session_state:
        st.session_state.selected_module = 'Module 1'
    if 'user_answer' not in st.session_state:
        st.session_state.user_answer = None
    if 'current_option_mapping' not in st.session_state:
        st.session_state.current_option_mapping = {}
    if 'current_question_id' not in st.session_state:
        st.session_state.current_question_id = None
    if 'answered_questions' not in st.session_state:
        st.session_state.answered_questions = set()

    
    try:
        conn = get_snowflake_connection()
        if not conn:
            st.error("No database connection")
            return
        
        # Module selection - use a form to prevent reruns on change
        with st.form("module_selection_form"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Retrieve available modules
                try:
                    df = pd.read_sql("SELECT DISTINCT MODULE FROM FLASHCARDS ORDER BY MODULE", conn)
                    modules = df['MODULE'].tolist() if not df.empty else ['Module 1']
                except Exception as e:
                    st.error(f"Error loading modules: {e}")
                    modules = ['Module 1']
                
                selected_module = st.selectbox("Select module:", modules, key="module_selector")
            
            with col2:
                st.write("###")
                load_new_questions = st.form_submit_button("🔄 Load New Questions", use_container_width=True)
            
            # Handle form submission
            if st.form_submit_button("Apply Selection", use_container_width=True, type="primary"):
                # Check if module changed
                if selected_module != st.session_state.selected_module:
                    st.session_state.selected_module = selected_module
                    st.session_state.question_queue = []
                    st.session_state.current_question_index = 0
                    st.session_state.answer_submitted = False
                    st.session_state.user_answer = None
                    st.session_state.current_option_mapping = {}
                    st.session_state.current_question_id = None
                
                # Handle load new questions
                if load_new_questions:
                    st.session_state.question_queue = []
                    st.session_state.current_question_index = 0
                    st.session_state.answer_submitted = False
                    st.session_state.user_answer = None
                    st.session_state.current_option_mapping = {}
                    st.session_state.current_question_id = None
        
        # Load questions if queue is empty or has only 1 question left
        if len(st.session_state.question_queue) <= 1:
            load_questions(conn, st.session_state.selected_module, 3)
        
        # Check if we have questions
        if not st.session_state.question_queue:
            # Check if we've answered all questions
            cursor = conn.cursor()
            # Build the IN clause for answered questions
            if st.session_state.answered_questions:
                answered_list = ', '.join(f"'{id}'" for id in st.session_state.answered_questions)
                answered_clause = f"COUNT(CASE WHEN ID IN ({answered_list}) THEN 1 END)"
            else:
                answered_clause = "0"
            
            cursor.execute(f"""
                SELECT COUNT(*) as total,
                       {answered_clause} as answered
                FROM FLASHCARDS 
                WHERE MODULE = '{st.session_state.selected_module}'
            """)
            total, answered = cursor.fetchone()
            cursor.close()
            
            if total == answered:
                st.success(f"🎉 Congratulations! You've completed all questions in {st.session_state.selected_module}")
                if st.button("🔄 Reset Progress and Start Over"):
                    st.session_state.answered_questions = set()
                    st.rerun()
            else:
                st.warning(f"No more questions available for {st.session_state.selected_module}")
            return
        
        # Get current question
        current_question = st.session_state.question_queue[st.session_state.current_question_index]
        
        # Check if question changed - reset state if it did
        if st.session_state.current_question_id != current_question['ID']:
            st.session_state.current_question_id = current_question['ID']
            st.session_state.answer_submitted = False
            st.session_state.user_answer = None
            st.session_state.current_option_mapping = {}
            st.session_state.question_start_time = time.time()
        
        # Display progress
        progress_text = f"Question {st.session_state.current_question_index + 1} of {len(st.session_state.question_queue)}"
        if len(st.session_state.question_queue) <= 1:
            progress_text += " 🔄 Loading more questions soon..."
        st.caption(progress_text)
        
        # Display current question
        st.subheader(f"Question for {st.session_state.selected_module}")
        
        # Question card
        with st.container():
            st.markdown(f"### ❓ {current_question['QUESTION_TEXT']}")
            
            # Get randomized options and mapping (only if not already set for this question)
            if not st.session_state.current_option_mapping:
                options_list, option_mapping = get_randomized_options(current_question)
                st.session_state.current_option_mapping = option_mapping
            else:
                # Recreate options list from the stored mapping
                options_list = list(st.session_state.current_option_mapping.keys())
            
            # Display options without letters - just the text
            selected_option_text = st.radio(
                "Select your answer:", 
                options_list,
                index=options_list.index(st.session_state.user_answer) if st.session_state.user_answer in options_list else 0,
                key=f"answer_radio_{current_question['ID']}",
                disabled=st.session_state.answer_submitted
            )
            
            # Update user answer when selection changes
            if not st.session_state.answer_submitted:
                st.session_state.user_answer = selected_option_text
            
            # Action buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                # Only enable Check Answer if an answer is selected and not already submitted
                check_disabled = st.session_state.answer_submitted or st.session_state.user_answer is None
                
                if st.button(
                    "✅ Check Answer", 
                    disabled=check_disabled,
                    type="primary",
                    key=f"check_button_{current_question['ID']}",
                    use_container_width=True
                ):
                    handle_answer_check(current_user, current_question, conn)
            
            with col2:
                if st.button(
                    "➡️ Next Question", 
                    key=f"next_button_{current_question['ID']}",
                    use_container_width=True
                ):
                    # Move to next question
                    if st.session_state.current_question_index < len(st.session_state.question_queue) - 1:
                        st.session_state.current_question_index += 1
                    else:
                        # If we're at the end, clear the queue to trigger new questions load
                        st.session_state.question_queue = []
                        st.session_state.current_question_index = 0
                    
                    # Reset question state
                    st.session_state.answer_submitted = False
                    st.session_state.user_answer = None
                    st.session_state.current_option_mapping = {}
                    st.session_state.current_question_id = None
                    st.session_state.question_start_time = time.time()
                    
                    # Use st.rerun() to refresh the page with new question
                    st.rerun()
            
            with col3:
                if st.button(
                    "📊 View Statistics", 
                    key=f"stats_button_{current_question['ID']}",
                    use_container_width=True
                ):
                    show_question_statistics(conn, current_question)
                

        
        # Display user progress for the module (outside the form to avoid rerun issues)

        if st.checkbox("Show My Progress in This Module", key="progress_checkbox"):
            show_user_progress(conn, current_user, st.session_state.selected_module)
                        
    except Exception as e:
        st.error(f"Error in study mode: {e}")

def handle_answer_check(current_user, current_question, conn):
    """Handle answer checking logic"""
    # Start timer if not already started
    if st.session_state.question_start_time is None:
        st.session_state.question_start_time = time.time()
    
    # Calculate time spent
    time_spent = int(time.time() - st.session_state.question_start_time)
    
    # Check if answer is correct using the mapping
    user_selected_letter = st.session_state.current_option_mapping[st.session_state.user_answer]
    is_correct = (user_selected_letter == current_question['CORRECT_ANSWER'])
    
    # Display result
    if is_correct:
        st.success("🎉 Correct!")
    else:
        # Find the correct option text
        correct_option_text = get_key_from_value(st.session_state.current_option_mapping, current_question['CORRECT_ANSWER'])
        st.error(f"❌ Incorrect. The correct answer is: {correct_option_text}")
    
    # Show explanation if available
    if current_question['EXPLANATION']:
        st.info(f"💡 **Explanation:** {current_question['EXPLANATION']}")
    
    # Save progress to database
    try:
        cursor = conn.cursor()
        insert_query = """
            INSERT INTO PROGRESS_TRACKING 
            (USER_ID, QUESTION_ID, USER_ANSWER, IS_CORRECT, TIME_SECONDS, MODULE)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            current_user['user_id'],
            current_question['ID'],
            user_selected_letter,  # Store the letter (A, B, C, D) for tracking
            is_correct,
            time_spent,
            st.session_state.selected_module
        ))
        conn.commit()
        cursor.close()
    except Exception as e:
        st.error(f"Error saving progress: {e}")
    
    st.session_state.answer_submitted = True
    # Add question to answered set
    st.session_state.answered_questions.add(current_question['ID'])
    
    # Remove current question from queue
    if len(st.session_state.question_queue) > 1:  # Keep at least one question
        st.session_state.question_queue.pop(st.session_state.current_question_index)
        # Adjust index if we removed a question before the current index
        if st.session_state.current_question_index >= len(st.session_state.question_queue):
            st.session_state.current_question_index = len(st.session_state.question_queue) - 1

def get_randomized_options(question):
    """Get options in randomized order while preserving correct answer mapping"""
    options = {
        'A': question['OPTION_A'],
        'B': question['OPTION_B'],
        'C': question['OPTION_C'],
        'D': question['OPTION_D']
    }
    
    # Create a list of option letters and shuffle them
    option_letters = list(options.keys())
    random.shuffle(option_letters)
    
    # Create new mapping with shuffled letters but same option texts
    shuffled_options_text_to_letter = {}
    for old_letter in option_letters:
        shuffled_options_text_to_letter[options[old_letter]] = old_letter
    
    # Return the list of option texts (for display) and the mapping (for validation)
    option_texts = list(shuffled_options_text_to_letter.keys())
    return option_texts, shuffled_options_text_to_letter

def get_key_from_value(dictionary, target_value):
    """Helper function to get key from value in a dictionary"""
    for key, value in dictionary.items():
        if value == target_value:
            return key
    return None

def load_questions(conn, module, count=3):
    """Load questions into the queue"""
    try:
        # Build the NOT IN clause only if there are answered questions
        if st.session_state.answered_questions:
            answered_list = ', '.join(f"'{id}'" for id in st.session_state.answered_questions)
            not_in_clause = f"AND ID NOT IN ({answered_list})"
        else:
            not_in_clause = ""
        
        query = f"""
            SELECT * FROM FLASHCARDS 
            WHERE MODULE = '{module}'
            {not_in_clause}
            ORDER BY RANDOM() 
            LIMIT {count}
        """
        df = pd.read_sql(query, conn)
        
        if not df.empty:
            # Convert DataFrame to list of dictionaries
            new_questions = df.to_dict('records')
            st.session_state.question_queue.extend(new_questions)
        else:
            st.error(f"No questions found for module: {module}")
            
    except Exception as e:
        st.error(f"Error loading questions: {e}")

def move_to_next_question():
    """Move to the next question in the queue"""
    # Reset all question-specific state
    st.session_state.answer_submitted = False
    st.session_state.user_answer = None
    st.session_state.current_option_mapping = {}
    st.session_state.current_question_id = None
    st.session_state.question_start_time = time.time()
    
    # Move to next question
    if st.session_state.current_question_index < len(st.session_state.question_queue) - 1:
        st.session_state.current_question_index += 1
    else:
        # If we're at the end, clear the queue to trigger new questions load
        st.session_state.question_queue = []
        st.session_state.current_question_index = 0

def show_question_statistics(conn, question):
    """Show statistics for the current question"""
    try:
        stats_query = f"""
            SELECT 
                COUNT(*) as total_attempts,
                SUM(CASE WHEN IS_CORRECT THEN 1 ELSE 0 END) as correct_attempts,
                ROUND(AVG(TIME_SECONDS), 1) as avg_time_seconds
            FROM PROGRESS_TRACKING 
            WHERE QUESTION_ID = '{question['ID']}'
        """
        stats_df = pd.read_sql(stats_query, conn)
        
        if not stats_df.empty:
            total = stats_df.iloc[0]['TOTAL_ATTEMPTS']
            correct = stats_df.iloc[0]['CORRECT_ATTEMPTS']
            avg_time = stats_df.iloc[0]['AVG_TIME_SECONDS']
            
            if total > 0:
                accuracy = (correct / total) * 100
                st.info(f"""
                **Question Statistics:**
                - 📊 **Accuracy:** {accuracy:.1f}% ({correct}/{total})
                - ⏱️ **Average Time:** {avg_time}s
                - 🎯 **Difficulty:** {'Easy' if accuracy > 70 else 'Medium' if accuracy > 40 else 'Hard'}
                """)
            else:
                st.info("No statistics available for this question yet.")
        else:
            st.info("No statistics available for this question.")
    except Exception as e:
        st.error(f"Error loading statistics: {e}")

def show_user_progress(conn, current_user, selected_module):
    """Show user progress for the current module"""
    try:
        progress_query = f"""
            SELECT 
                COUNT(*) as total_answered,
                SUM(CASE WHEN IS_CORRECT THEN 1 ELSE 0 END) as correct_answers,
                ROUND(SUM(CASE WHEN IS_CORRECT THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as accuracy_percentage,
                ROUND(AVG(TIME_SECONDS), 1) as avg_time_seconds
            FROM PROGRESS_TRACKING 
            WHERE USER_ID = '{current_user['user_id']}' AND MODULE = '{selected_module}'
        """
        progress_df = pd.read_sql(progress_query, conn)
        
        if not progress_df.empty and progress_df.iloc[0]['TOTAL_ANSWERED'] > 0:
            progress = progress_df.iloc[0]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Answered", progress['TOTAL_ANSWERED'])
            with col2:
                st.metric("Accuracy", f"{progress['ACCURACY_PERCENTAGE']}%")
            with col3:
                st.metric("Avg Time", f"{progress['AVG_TIME_SECONDS']}s")
        else:
            st.info("No progress recorded for this module yet.")
    except Exception as e:
        st.error(f"Error loading progress: {e}")

if __name__ == "__main__":
    show_study()