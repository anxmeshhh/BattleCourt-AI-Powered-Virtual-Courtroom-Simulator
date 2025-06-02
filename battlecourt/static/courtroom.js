// Courtroom JavaScript
let trialData = null;
let currentRound = 1;
let isLegalHelpVisible = false;
let isSubmitting = false;

// Initialize courtroom when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Get trial data from sessionStorage
    const storedData = sessionStorage.getItem('trialData');
    if (storedData) {
        trialData = JSON.parse(storedData);
        initializeCourtroom();
    } else {
        // Redirect back to setup if no trial data
        window.location.href = '/';
    }
    
    // Setup character counter
    const textarea = document.getElementById('user-statement');
    const charCount = document.getElementById('char-count');
    
    textarea.addEventListener('input', function() {
        const count = this.value.length;
        charCount.textContent = count;
        
        if (count > 1000) {
            charCount.style.color = '#e74c3c';
        } else if (count > 800) {
            charCount.style.color = '#f39c12';
        } else {
            charCount.style.color = '#7f8c8d';
        }
    });
    
    // Setup keyboard shortcuts
    textarea.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.key === 'Enter') {
            e.preventDefault();
            submitTurn();
        }
    });
});

function initializeCourtroom() {
    if (!trialData) return;
    
    // Update header information
    document.getElementById('case-title').textContent = trialData.case;
    document.getElementById('round-counter').textContent = `Round ${trialData.current_round} of ${trialData.total_rounds}`;
    document.getElementById('user-role-display').textContent = `You are the ${trialData.user_role}`;
    
    // Update case strength bars
    updateCaseStrength(trialData.case_strength);
    
    // Display initial AI statement
    if (trialData.ai_statement) {
        addMessageToChat(trialData.ai_role, trialData.ai_statement, 'opening_statement');
    }
    
    // Display judge comment
    if (trialData.judge_comment) {
        addJudgeComment(trialData.judge_comment);
    }
    
    // Display jury reaction
    if (trialData.jury_reaction) {
        addJuryReaction(trialData.jury_reaction);
    }
    
    // Display evidence and witnesses
    displayEvidence(trialData.evidence);
    displayWitnesses(trialData.witnesses);
    
    // Display legal help if available
    if (trialData.legal_help) {
        updateLegalHelp(trialData.legal_help);
    }
    
    // Show input section
    document.getElementById('input-section').style.display = 'block';
}

function addMessageToChat(role, message, type = 'statement') {
    const timestamp = new Date().toLocaleTimeString();
    const isUser = role === trialData.user_role;
    
    // Determine which chat section to use
    let chatContainer;
    if (role === 'Prosecutor' || role.includes('Prosecution')) {
        chatContainer = document.getElementById('prosecution-chat');
    } else if (role === 'Defense Attorney' || role.includes('Defense')) {
        chatContainer = document.getElementById('defense-chat');
    } else {
        // Default to user's role chat
        chatContainer = trialData.user_role === 'Prosecutor' ? 
            document.getElementById('prosecution-chat') : 
            document.getElementById('defense-chat');
    }
    
    // Remove placeholder if it exists
    const placeholder = chatContainer.querySelector('.chat-placeholder');
    if (placeholder) {
        placeholder.remove();
    }
    
    // Create message element
    const messageDiv = document.createElement('div');
    messageDiv.className = 'chat-message fade-in';
    
    const typeIcon = getTypeIcon(type);
    const roleIcon = getRoleIcon(role);
    
    messageDiv.innerHTML = `
        <div class="message-header">
            <span class="message-role">${roleIcon} ${role}</span>
            <span class="message-time">${typeIcon} ${timestamp}</span>
        </div>
        <div class="message-content">${formatMessage(message)}</div>
    `;
    
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function addJudgeComment(comment) {
    const timestamp = new Date().toLocaleTimeString();
    const judgeComments = document.getElementById('judge-comments');
    
    // Remove placeholder if it exists
    const placeholder = judgeComments.querySelector('.comment-placeholder');
    if (placeholder) {
        placeholder.remove();
    }
    
    const commentDiv = document.createElement('div');
    commentDiv.className = 'judge-comment fade-in';
    commentDiv.innerHTML = `
        <div class="comment-header">
            <span class="comment-time">👨‍⚖️ ${timestamp}</span>
        </div>
        <div class="comment-text">${formatMessage(comment)}</div>
    `;
    
    judgeComments.appendChild(commentDiv);
    judgeComments.scrollTop = judgeComments.scrollHeight;
}

function addJuryReaction(reaction) {
    const timestamp = new Date().toLocaleTimeString();
    const juryReactions = document.getElementById('jury-reactions');
    
    // Remove placeholder if it exists
    const placeholder = juryReactions.querySelector('.reaction-placeholder');
    if (placeholder) {
        placeholder.remove();
    }
    
    const reactionDiv = document.createElement('div');
    reactionDiv.className = 'jury-reaction fade-in';
    reactionDiv.innerHTML = `
        <div class="reaction-header">
            <span class="reaction-time">👥 ${timestamp}</span>
        </div>
        <div class="reaction-text">${formatMessage(reaction)}</div>
    `;
    
    juryReactions.appendChild(reactionDiv);
    juryReactions.scrollTop = juryReactions.scrollHeight;
}

function displayEvidence(evidence) {
    const evidenceList = document.getElementById('evidence-list');
    evidenceList.innerHTML = '';
    
    if (evidence && evidence.length > 0) {
        evidence.forEach((item, index) => {
            const evidenceDiv = document.createElement('div');
            evidenceDiv.className = 'evidence-item fade-in';
            evidenceDiv.style.animationDelay = `${index * 0.1}s`;
            evidenceDiv.innerHTML = `
                <div class="evidence-number">Evidence ${index + 1}</div>
                <div class="evidence-description">${typeof item === 'string' ? item : item.description || item}</div>
            `;
            evidenceList.appendChild(evidenceDiv);
        });
    } else {
        evidenceList.innerHTML = '<div class="loading">No evidence available</div>';
    }
}

function displayWitnesses(witnesses) {
    const witnessList = document.getElementById('witness-list');
    witnessList.innerHTML = '';
    
    if (witnesses && witnesses.length > 0) {
        witnesses.forEach((witness, index) => {
            const witnessDiv = document.createElement('div');
            witnessDiv.className = 'witness-item fade-in';
            witnessDiv.style.animationDelay = `${index * 0.1}s`;
            
            if (typeof witness === 'string') {
                witnessDiv.innerHTML = `
                    <div class="witness-name">Witness ${index + 1}</div>
                    <div class="witness-description">${witness}</div>
                `;
            } else {
                witnessDiv.innerHTML = `
                    <div class="witness-name">${witness.name || `Witness ${index + 1}`}</div>
                    <div class="witness-role">${witness.role || 'Witness'}</div>
                    <div class="witness-description">${witness.description || witness.testimony || 'No description available'}</div>
                `;
            }
            
            witnessList.appendChild(witnessDiv);
        });
    } else {
        witnessList.innerHTML = '<div class="loading">No witnesses available</div>';
    }
}

function updateCaseStrength(strength) {
    const prosecutionBar = document.getElementById('prosecution-strength');
    const defenseBar = document.getElementById('defense-strength');
    
    if (strength) {
        prosecutionBar.style.width = `${strength.prosecution}%`;
        defenseBar.style.width = `${strength.defense}%`;
    }
}

function updateLegalHelp(helpContent) {
    const helpContentDiv = document.getElementById('help-content');
    helpContentDiv.innerHTML = formatMessage(helpContent);
}

async function submitTurn() {
    if (isSubmitting) return;
    
    const statement = document.getElementById('user-statement').value.trim();
    const actionType = document.getElementById('action-type').value;
    
    if (!statement) {
        alert('Please enter your argument, objection, or question.');
        return;
    }
    
    if (statement.length > 1000) {
        alert('Your statement is too long. Please keep it under 1000 characters.');
        return;
    }
    
    isSubmitting = true;
    
    // Add user's message to chat immediately
    addMessageToChat(trialData.user_role, statement, actionType);
    
    // Clear input and disable form
    document.getElementById('user-statement').value = '';
    document.getElementById('char-count').textContent = '0';
    document.getElementById('input-section').style.display = 'none';
    document.getElementById('loading-overlay').style.display = 'flex';
    
    try {
        const formData = new FormData();
        formData.append('statement', statement);
        formData.append('action_type', actionType);
        
        const response = await fetch('/submit_turn', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            if (data.trial_ended) {
                showVerdict(data);
            } else {
                // Add AI response
                if (data.ai_statement) {
                    addMessageToChat(trialData.ai_role, data.ai_statement, 'response');
                }
                
                // Add judge comment
                if (data.judge_comment) {
                    addJudgeComment(data.judge_comment);
                }
                
                // Add jury reaction
                if (data.jury_reaction) {
                    addJuryReaction(data.jury_reaction);
                }
                
                // Update legal help
                if (data.legal_help) {
                    updateLegalHelp(data.legal_help);
                }
                
                // Update case strength
                if (data.case_strength) {
                    updateCaseStrength(data.case_strength);
                }
                
                // Update round counter
                if (data.current_round) {
                    currentRound = data.current_round;
                    document.getElementById('round-counter').textContent = `Round ${currentRound} of ${trialData.total_rounds}`;
                }
                
                // Re-enable input
                document.getElementById('input-section').style.display = 'block';
            }
        } else {
            alert('Error: ' + (data.error || 'Unknown error occurred'));
            document.getElementById('input-section').style.display = 'block';
        }
    } catch (error) {
        console.error('Error submitting turn:', error);
        alert('Network error. Please try again.');
        document.getElementById('input-section').style.display = 'block';
    } finally {
        document.getElementById('loading-overlay').style.display = 'none';
        isSubmitting = false;
    }
}

function showVerdict(data) {
    const verdictSection = document.getElementById('verdict-section');
    const verdictContent = document.getElementById('verdict-content');
    
    verdictContent.innerHTML = `
        <div class="verdict-text">${formatMessage(data.verdict)}</div>
        <div class="verdict-summary">
            <h3>Case Summary</h3>
            <p><strong>Winner:</strong> ${data.winner}</p>
            <p><strong>Margin:</strong> ${data.margin}%</p>
            <p><strong>Total Rounds:</strong> ${data.total_rounds}</p>
            <p><strong>Final Strength:</strong> Prosecution ${data.case_strength.prosecution}% | Defense ${data.case_strength.defense}%</p>
        </div>
    `;
    
    verdictSection.style.display = 'flex';
}

function toggleLegalHelp() {
    const helpPanel = document.getElementById('legal-help-panel');
    const toggleBtn = document.getElementById('help-toggle-btn');
    
    isLegalHelpVisible = !isLegalHelpVisible;
    
    if (isLegalHelpVisible) {
        helpPanel.classList.add('active');
        toggleBtn.innerHTML = '<span class="help-icon">💡</span><span class="help-text">Hide Help</span>';
    } else {
        helpPanel.classList.remove('active');
        toggleBtn.innerHTML = '<span class="help-icon">💡</span><span class="help-text">Legal Help</span>';
    }
}

function startNewTrial() {
    sessionStorage.removeItem('trialData');
    window.location.href = '/';
}

function reviewCase() {
    document.getElementById('verdict-section').style.display = 'none';
    // Allow user to review the case transcript
}

// Utility functions
function formatMessage(message) {
    if (!message) return '';
    
    return message
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>');
}

function getTypeIcon(type) {
    const icons = {
        'opening_statement': '🎯',
        'statement': '💬',
        'objection': '⚠️',
        'cross_examination': '❓',
        'evidence': '📋',
        'response': '↩️'
    };
    return icons[type] || '💬';
}

function getRoleIcon(role) {
    if (role.includes('Prosecutor') || role.includes('Prosecution')) {
        return '⚔️';
    } else if (role.includes('Defense')) {
        return '🛡️';
    } else if (role.includes('Judge')) {
        return '👨‍⚖️';
    } else if (role.includes('Jury')) {
        return '👥';
    } else if (role.includes('Witness')) {
        return '👤';
    }
    return '💼';
}

// Add route for courtroom page