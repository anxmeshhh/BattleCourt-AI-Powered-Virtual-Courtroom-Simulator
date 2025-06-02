import os
import random
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import datetime

app = Flask(__name__)

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini 2.0 Flash model
model = genai.GenerativeModel("gemini-2.0-flash")

# Sample case types with detailed information
case_types = [
    {
        "title": "Criminal Case: Murder under Section 300 IPC",
        "description": "A high-profile murder case involving complex forensic evidence and multiple witnesses.",
        "complexity": "High",
        "estimated_duration": "8 rounds",
        "background": "The accused allegedly murdered their business partner after a financial dispute. The prosecution claims premeditation, while the defense argues self-defense."
    },
    {
        "title": "Civil Case: Property Dispute under CPC",
        "description": "A contentious property dispute between family members over ancestral property rights.",
        "complexity": "Medium",
        "estimated_duration": "6 rounds",
        "background": "Two siblings are contesting the ownership of a family property worth ₹2 crore, with conflicting interpretations of their father's will."
    },
    {
        "title": "Criminal Case: Cheating under Section 420 IPC",
        "description": "A financial fraud case involving multiple victims and complex paper trails.",
        "complexity": "Medium",
        "estimated_duration": "6 rounds",
        "background": "The accused allegedly defrauded over 50 investors through a fake investment scheme, promising unrealistic returns."
    },
    {
        "title": "Family Law: Maintenance under Section 125 CrPC",
        "description": "A maintenance case involving complex financial disclosures and child custody issues.",
        "complexity": "Low",
        "estimated_duration": "5 rounds",
        "background": "A divorced spouse is seeking maintenance for herself and two minor children, claiming the ex-spouse is hiding assets."
    },
    {
        "title": "Contract Law: Breach under Indian Contract Act, 1872",
        "description": "A corporate dispute over alleged breach of a high-value service contract.",
        "complexity": "High",
        "estimated_duration": "7 rounds",
        "background": "A tech company is suing a client for unpaid services worth ₹5 crore, while the client claims the deliverables were substandard."
    },
    {
        "title": "Cyber Crime: Data Theft under IT Act, 2000",
        "description": "A modern case involving corporate espionage and digital evidence.",
        "complexity": "High",
        "estimated_duration": "8 rounds",
        "background": "An ex-employee is accused of stealing proprietary algorithms valued at ₹10 crore from their former employer."
    }
]

# Lawyer personality tones
lawyer_tones = {
    "serious": "Formal and strictly professional, focuses on facts and legal precedents",
    "passionate": "Emotionally engaging, uses powerful rhetoric and appeals to moral principles",
    "analytical": "Logical and methodical, breaks down complex arguments with precision",
    "aggressive": "Confrontational and assertive, challenges opposing arguments directly",
    "diplomatic": "Balanced and respectful, finds common ground while making strong points"
}

# Trial state
trial_state = {
    "case": None,
    "case_background": None,
    "user_role": None,
    "ai_role": None,
    "user_tone": None,
    "ai_tone": None,
    "turns": [],
    "current_turn": "AI",
    "is_trial_active": False,
    "legal_help": True,
    "witnesses": [],
    "evidence": [],
    "objections": [],
    "current_round": 1,
    "total_rounds": 6,
    "case_strength": {"prosecution": 50, "defense": 50}
}

@app.route("/")
def index():
    return render_template("index.html", case_types=case_types, lawyer_tones=lawyer_tones)

@app.route("/start_trial", methods=["POST"])
def start_trial():
    global trial_state
    
    # Get form data
    case_index = int(request.form.get("case_index", 0))
    selected_case = case_types[case_index]
    
    trial_state["case"] = selected_case["title"]
    trial_state["case_background"] = selected_case["background"]
    trial_state["user_role"] = request.form.get("role")
    trial_state["ai_role"] = "Defense Attorney" if trial_state["user_role"] == "Prosecutor" else "Prosecutor"
    trial_state["user_tone"] = request.form.get("user_tone", "serious")
    trial_state["ai_tone"] = request.form.get("ai_tone", "aggressive")
    trial_state["turns"] = []
    trial_state["witnesses"] = []
    trial_state["evidence"] = []
    trial_state["objections"] = []
    trial_state["is_trial_active"] = True
    trial_state["current_turn"] = "AI"
    trial_state["current_round"] = 1
    trial_state["legal_help"] = request.form.get("legal_help", "true") == "true"
    trial_state["total_rounds"] = int(selected_case["estimated_duration"].split()[0])
    trial_state["case_strength"] = {"prosecution": 50, "defense": 50}
    
    # Generate witnesses
    witness_prompt = f"""
    For the case: {trial_state['case']}, under the Indian legal system, generate 3-4 witness profiles relevant to the case. 
    Each profile should include name, role (e.g., eyewitness, expert), and a brief description of their testimony. 
    Ensure alignment with Indian laws (e.g., IPC, CrPC) and the case background: {trial_state['case_background']}.
    Format each witness as a JSON object with name, role, and testimony fields.
    """
    witness_response = model.generate_content(witness_prompt)
    
    # Process witness response - handle potential formatting issues
    try:
        import re
        import json
        
        # Extract JSON-like structures from the text
        witness_text = witness_response.text
        json_pattern = r'\{[^{}]*\}'
        json_matches = re.findall(json_pattern, witness_text, re.DOTALL)
        
        witnesses = []
        for match in json_matches[:4]:  # Limit to 4 witnesses
            try:
                witness = json.loads(match)
                witnesses.append(witness)
            except json.JSONDecodeError:
                # If JSON parsing fails, create a simple object
                witnesses.append({"name": "Witness", "role": "Relevant Witness", "testimony": match})
        
        if not witnesses:
            # Fallback if no JSON structures found
            witness_parts = witness_text.split("\n\n")
            for part in witness_parts[:4]:
                if part.strip():
                    witnesses.append({"name": "Witness", "role": "Relevant Witness", "testimony": part})
        
        trial_state["witnesses"] = witnesses
    except Exception as e:
        # Ultimate fallback
        print(f"Error processing witnesses: {e}")
        trial_state["witnesses"] = [{"name": "Witness 1", "role": "Key Witness", "testimony": "Has relevant information about the case."}]
    
    # Generate evidence
    evidence_prompt = f"""
    For the case: {trial_state['case']}, under the Indian legal system, generate 3-4 pieces of evidence relevant to the case.
    Each piece should include a brief description and its significance to the case.
    Ensure alignment with Indian laws (e.g., IPC, CrPC) and the case background: {trial_state['case_background']}.
    """
    evidence_response = model.generate_content(evidence_prompt)
    
    # Process evidence - simple approach
    evidence_items = evidence_response.text.split("\n\n")
    trial_state["evidence"] = [item for item in evidence_items if item.strip()][:4]
    
    # Generate AI's opening statement
    tone_instruction = get_tone_instruction(trial_state["ai_tone"])
    
    prompt = f"""
    You are an expert {trial_state['ai_role']} in an Indian courtroom, adhering to the Indian Constitution, IPC, CrPC, and legal precedents. 
    Case: {trial_state['case']}
    Case Background: {trial_state['case_background']}
    
    {tone_instruction}
    
    Deliver a formal opening statement for the {trial_state['ai_role']}, citing specific articles (e.g., Article 21), 
    sections (e.g., Section 300 IPC), and precedents (e.g., Maneka Gandhi v. Union of India). 
    Include logical arguments and anticipate objections. Keep it concise (under 300 words) and professional.
    """
    response = model.generate_content(prompt)
    ai_statement = response.text
    
    # Generate judge's initial comment
    judge_prompt = f"""
    You are an impartial judge in an Indian courtroom. The case before you is:
    {trial_state['case']}
    {trial_state['case_background']}
    
    Provide a brief opening remark as the judge, setting expectations for the trial and reminding both counsels 
    about courtroom decorum and the importance of evidence-based arguments. Keep it under 100 words.
    """
    judge_response = model.generate_content(judge_prompt)
    judge_comment = judge_response.text
    
    # Generate jury's initial reaction
    jury_prompt = f"""
    You are representing the collective thoughts of a jury in an Indian courtroom. The case before you is:
    {trial_state['case']}
    {trial_state['case_background']}
    
    Provide a brief initial impression from the jury's perspective before any arguments are made.
    Express neutrality and willingness to hear both sides. Keep it under 80 words.
    """
    jury_response = model.generate_content(jury_prompt)
    jury_reaction = jury_response.text
    
    # Generate legal help
    if trial_state["legal_help"]:
        help_prompt = f"""
        For the case: {trial_state['case']}, as the {trial_state['user_role']}, provide clear, layperson-friendly legal advice 
        for responding to the opening statement. The case background is: {trial_state['case_background']}
        
        Cite specific articles (e.g., Article 21), sections (e.g., Section 300 IPC), and precedents. 
        Explain why certain approaches are optimal and suggest 2-3 future steps (e.g., call witness, raise objection). 
        Keep it dynamic and context-aware. Format with bullet points for readability.
        """
        legal_help_response = model.generate_content(help_prompt)
        legal_help = legal_help_response.text
    else:
        legal_help = ""
    
    # Record the AI's opening statement
    trial_state["turns"].append({
        "role": trial_state["ai_role"],
        "statement": ai_statement,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "type": "opening_statement"
    })
    
    return jsonify({
        "success": True,
        "case": trial_state["case"],
        "case_background": trial_state["case_background"],
        "user_role": trial_state["user_role"],
        "ai_role": trial_state["ai_role"],
        "ai_statement": ai_statement,
        "judge_comment": judge_comment,
        "jury_reaction": jury_reaction,
        "legal_help": legal_help,
        "current_turn": trial_state["current_turn"],
        "current_round": trial_state["current_round"],
        "total_rounds": trial_state["total_rounds"],
        "witnesses": trial_state["witnesses"],
        "evidence": trial_state["evidence"],
        "case_strength": trial_state["case_strength"]
    })

@app.route("/submit_turn", methods=["POST"])
def submit_turn():
    global trial_state
    if not trial_state["is_trial_active"]:
        return jsonify({"success": False, "error": "No active trial"}), 400
    
    user_statement = request.form.get("statement")
    action_type = request.form.get("action_type", "statement")
    
    # Record user's statement
    trial_state["turns"].append({
        "role": trial_state["user_role"],
        "statement": user_statement,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "type": action_type
    })
    
    # Update case strength based on user's argument quality
    quality_prompt = f"""
    Evaluate the quality of this {action_type} in the context of the case:
    Case: {trial_state['case']}
    Background: {trial_state['case_background']}
    Statement: "{user_statement}"
    Role: {trial_state['user_role']}
    
    On a scale of 1-10, how effective is this argument legally? Only respond with a number.
    """
    quality_response = model.generate_content(quality_prompt)
    try:
        quality_score = int(quality_response.text.strip())
    except:
        quality_score = 5  # Default if parsing fails
    
    # Adjust case strength
    strength_change = (quality_score - 5) * 2  # -10 to +10 change
    if trial_state["user_role"] == "Prosecutor":
        trial_state["case_strength"]["prosecution"] = min(100, trial_state["case_strength"]["prosecution"] + strength_change)
        trial_state["case_strength"]["defense"] = max(0, trial_state["case_strength"]["defense"] - strength_change)
    else:
        trial_state["case_strength"]["defense"] = min(100, trial_state["case_strength"]["defense"] + strength_change)
        trial_state["case_strength"]["prosecution"] = max(0, trial_state["case_strength"]["prosecution"] - strength_change)
    
    # Handle different action types
    if action_type == "objection":
        trial_state["objections"].append({
            "role": trial_state["user_role"],
            "statement": user_statement,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        
        # Generate judge's ruling on objection
        judge_prompt = f"""
        You are an impartial judge in an Indian courtroom, adhering to the Indian Constitution, IPC, CrPC, and precedents. 
        Case: {trial_state['case']}
        Background: {trial_state['case_background']}
        
        The {trial_state['user_role']} has raised an objection: '{user_statement}'
        
        Rule on the objection, citing specific laws or precedents (e.g., Section 151 CPC for procedure). 
        Explain your ruling clearly and concisely. Keep it under 150 words.
        """
        judge_response = model.generate_content(judge_prompt)
        judge_comment = judge_response.text
        
        # Generate jury reaction to objection
        jury_prompt = f"""
        You are representing the collective thoughts of a jury in an Indian courtroom.
        Case: {trial_state['case']}
        Background: {trial_state['case_background']}
        
        The {trial_state['user_role']} has raised an objection: '{user_statement}'
        The judge has ruled: '{judge_comment}'
        
        Provide a brief reaction from the jury's perspective. How does this objection and ruling affect their view?
        Keep it under 80 words and focus on the jury's impression.
        """
        jury_response = model.generate_content(jury_prompt)
        jury_reaction = jury_response.text
        
        # AI doesn't respond directly to objections
        ai_statement = None
        
    elif action_type == "cross_examination":
        # Determine which witness is being examined
        witness_prompt = f"""
        Based on this cross-examination question: '{user_statement}'
        Which of these witnesses is most likely being addressed?
        Witnesses: {trial_state['witnesses']}
        
        Respond with just the index number (0, 1, 2, etc.) of the most relevant witness.
        """
        witness_response = model.generate_content(witness_prompt)
        try:
            witness_index = int(witness_response.text.strip())
            if witness_index >= len(trial_state["witnesses"]):
                witness_index = 0
        except:
            witness_index = 0
        
        witness = trial_state["witnesses"][witness_index]
        
        # Generate witness response
        witness_prompt = f"""
        You are a witness in an Indian courtroom for the case: {trial_state['case']}
        Your profile: {witness}
        
        The {trial_state['user_role']} is cross-examining you with: '{user_statement}'
        
        Respond as the witness, providing testimony consistent with your profile and the case background: {trial_state['case_background']}
        Reference relevant laws if applicable. The response should be concise (under 150 words) and realistic.
        """
        witness_response = model.generate_content(witness_prompt)
        ai_statement = witness_response.text
        
        # Generate judge comment on cross-examination
        judge_prompt = f"""
        You are an impartial judge in an Indian courtroom.
        Case: {trial_state['case']}
        
        The {trial_state['user_role']} has cross-examined a witness with: '{user_statement}'
        The witness responded: '{ai_statement}'
        
        Provide a brief comment on the cross-examination process. Was it effective? Any procedural notes?
        Keep it under 80 words.
        """
        judge_response = model.generate_content(judge_prompt)
        judge_comment = judge_response.text
        
        # Generate jury reaction
        jury_prompt = f"""
        You are representing the collective thoughts of a jury in an Indian courtroom.
        Case: {trial_state['case']}
        
        The {trial_state['user_role']} has cross-examined a witness with: '{user_statement}'
        The witness responded: '{ai_statement}'
        
        Provide a brief reaction from the jury's perspective. How credible was the witness? How effective was the questioning?
        Keep it under 80 words.
        """
        jury_response = model.generate_content(jury_prompt)
        jury_reaction = jury_response.text
        
    elif action_type == "evidence":
        # Add new evidence if provided
        if user_statement and len(user_statement) > 10:
            trial_state["evidence"].append(user_statement)
        
        # Generate judge comment on evidence
        judge_prompt = f"""
        You are an impartial judge in an Indian courtroom.
        Case: {trial_state['case']}
        
        The {trial_state['user_role']} has presented evidence: '{user_statement}'
        
        Comment on the admissibility and relevance of this evidence according to Indian Evidence Act.
        Keep it under 100 words.
        """
        judge_response = model.generate_content(judge_prompt)
        judge_comment = judge_response.text
        
        # Generate AI response to evidence
        tone_instruction = get_tone_instruction(trial_state["ai_tone"])
        
        ai_prompt = f"""
        You are an expert {trial_state['ai_role']} in an Indian courtroom.
        Case: {trial_state['case']}
        Background: {trial_state['case_background']}
        
        {tone_instruction}
        
        The {trial_state['user_role']} has presented evidence: '{user_statement}'
        
        Respond to this evidence from your role's perspective. Challenge or acknowledge it as appropriate.
        Cite relevant laws or precedents. Keep it under 200 words.
        """
        ai_response = model.generate_content(ai_prompt)
        ai_statement = ai_response.text
        
        # Generate jury reaction
        jury_prompt = f"""
        You are representing the collective thoughts of a jury in an Indian courtroom.
        Case: {trial_state['case']}
        
        The {trial_state['user_role']} has presented evidence: '{user_statement}'
        
        Provide a brief reaction from the jury's perspective. How compelling is this evidence?
        Keep it under 80 words.
        """
        jury_response = model.generate_content(jury_prompt)
        jury_reaction = jury_response.text
        
    else:  # Regular statement
        # Generate AI's response
        tone_instruction = get_tone_instruction(trial_state["ai_tone"])
        
        prompt = f"""
        You are an expert {trial_state['ai_role']} in an Indian courtroom, adhering to the Indian Constitution, IPC, CrPC, and precedents. 
        Case: {trial_state['case']}
        Background: {trial_state['case_background']}
        
        {tone_instruction}
        
        The {trial_state['user_role']} stated: '{user_statement}'
        
        Respond with a counter-argument or supporting statement (depending on your role), citing specific articles, 
        sections, and precedents relevant to Indian law. Include logical, persuasive arguments.
        Keep it concise (under 250 words) and professional.
        """
        response = model.generate_content(prompt)
        ai_statement = response.text
        
        # Generate judge comment
        judge_prompt = f"""
        You are an impartial judge in an Indian courtroom.
        Case: {trial_state['case']}
        
        The {trial_state['user_role']} argued: '{user_statement}'
        The {trial_state['ai_role']} responded: '{ai_statement}'
        
        Provide a brief procedural comment or observation on the arguments presented.
        Keep it under 100 words and focus on legal procedure rather than the merits of the case.
        """
        judge_response = model.generate_content(judge_prompt)
        judge_comment = judge_response.text
        
        # Generate jury reaction
        jury_prompt = f"""
        You are representing the collective thoughts of a jury in an Indian courtroom.
        Case: {trial_state['case']}
        
        The {trial_state['user_role']} argued: '{user_statement}'
        The {trial_state['ai_role']} responded: '{ai_statement}'
        
        Provide a brief reaction from the jury's perspective. Which argument seemed more persuasive?
        Keep it under 80 words and focus on the jury's impression.
        """
        jury_response = model.generate_content(jury_prompt)
        jury_reaction = jury_response.text
    
    # Record AI's response if there is one
    if ai_statement:
        trial_state["turns"].append({
            "role": trial_state["ai_role"] if action_type != "cross_examination" else "Witness",
            "statement": ai_statement,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "type": "response"
        })
    
    # Generate legal help
    if trial_state["legal_help"]:
        help_prompt = f"""
        For the case: {trial_state['case']}, as the {trial_state['user_role']}, provide strategic legal advice 
        for the next round based on the current situation:
        
        Your last statement ({action_type}): '{user_statement}'
        
        {f"AI response: '{ai_statement}'" if ai_statement else ""}
        {f"Judge comment: '{judge_comment}'" if 'judge_comment' in locals() else ""}
        
        Case background: {trial_state['case_background']}
        Current case strength: Prosecution {trial_state['case_strength']['prosecution']}%, Defense {trial_state['case_strength']['defense']}%
        
        Provide specific legal strategies, citing relevant Indian laws and precedents.
        Suggest 2-3 concrete approaches for the next round.
        Format with bullet points for readability.
        """
        legal_help_response = model.generate_content(help_prompt)
        legal_help = legal_help_response.text
    else:
        legal_help = ""
    
    # Increment round counter
    trial_state["current_round"] += 1
    
    # Check if trial should end
    if trial_state["current_round"] > trial_state["total_rounds"]:
        return end_trial()
    
    return jsonify({
        "success": True,
        "ai_statement": ai_statement,
        "judge_comment": judge_comment if 'judge_comment' in locals() else None,
        "jury_reaction": jury_reaction if 'jury_reaction' in locals() else None,
        "legal_help": legal_help,
        "current_round": trial_state["current_round"],
        "case_strength": trial_state["case_strength"]
    })

def end_trial():
    global trial_state
    
    # Determine winner based on case strength
    if trial_state["case_strength"]["prosecution"] > trial_state["case_strength"]["defense"]:
        winner = "Prosecution"
        margin = trial_state["case_strength"]["prosecution"] - trial_state["case_strength"]["defense"]
    else:
        winner = "Defense"
        margin = trial_state["case_strength"]["defense"] - trial_state["case_strength"]["prosecution"]
    
    # Generate verdict
    verdict_prompt = f"""
    You are an impartial judge in an Indian courtroom, adhering to the Indian Constitution, IPC, CrPC, and precedents. 
    Case: {trial_state['case']}
    Background: {trial_state['case_background']}
    
    The trial has concluded with the following strength assessment:
    Prosecution: {trial_state['case_strength']['prosecution']}%
    Defense: {trial_state['case_strength']['defense']}%
    
    Based on this assessment, the {winner} has prevailed with a margin of {margin}%.
    
    Provide a detailed verdict as the judge, citing specific articles, sections, and precedents from Indian law.
    Include an evaluation of key arguments, evidence presented, and legal reasoning.
    Declare the final judgment and any sentencing or remedies as appropriate for this case.
    Format it as a formal judicial verdict with clear sections.
    """
    verdict_response = model.generate_content(verdict_prompt)
    verdict = verdict_response.text
    
    trial_state["is_trial_active"] = False
    
    return jsonify({
        "success": True,
        "trial_ended": True,
        "verdict": verdict,
        "winner": winner,
        "margin": margin,
        "case_strength": trial_state["case_strength"],
        "total_rounds": trial_state["current_round"] - 1
    })

@app.route("/courtroom")
def courtroom():
    return render_template("courtroom.html")

def get_tone_instruction(tone):
    """Generate specific instructions based on the selected tone"""
    tone_instructions = {
        "serious": "Maintain a formal and strictly professional tone. Focus on facts, legal precedents, and logical arguments. Avoid emotional appeals or colorful language.",
        "passionate": "Use emotionally engaging language and powerful rhetoric. Appeal to moral principles and justice while still maintaining legal rigor. Use vivid language and emphasize the human elements of the case.",
        "analytical": "Take a logical and methodical approach. Break down complex arguments with precision and clarity. Use structured reasoning and emphasize the technical aspects of the law.",
        "aggressive": "Be confrontational and assertive in your arguments. Directly challenge opposing viewpoints and use strong, confident language. Push your position forcefully while maintaining legal professionalism.",
        "diplomatic": "Maintain a balanced and respectful tone. Acknowledge valid points from the opposition while still making strong arguments for your position. Find common ground where possible."
    }
    return tone_instructions.get(tone, tone_instructions["serious"])

if __name__ == "__main__":
    app.run(debug=True)