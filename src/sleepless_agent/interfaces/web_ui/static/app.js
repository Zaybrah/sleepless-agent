// Configuration management for Sleepless Agent

let currentConfig = {};

// Load configuration from server
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        const data = await response.json();
        
        if (data.success) {
            currentConfig = data.config;
            populateForm(currentConfig);
        } else {
            showMessage('Error loading configuration: ' + data.error, 'error');
        }
    } catch (error) {
        showMessage('Error loading configuration: ' + error.message, 'error');
    }
}

// Populate form with configuration data
function populateForm(config) {
    // Claude Code settings
    if (config.claude_code) {
        document.getElementById('claude-binary').value = config.claude_code.binary_path || '';
        document.getElementById('claude-model').value = config.claude_code.model || '';
        document.getElementById('threshold-day').value = config.claude_code.threshold_day || '';
        document.getElementById('threshold-night').value = config.claude_code.threshold_night || '';
        document.getElementById('night-start').value = config.claude_code.night_start_hour || '';
        document.getElementById('night-end').value = config.claude_code.night_end_hour || '';
    }
    
    // Git settings
    if (config.git) {
        document.getElementById('git-use-remote').checked = config.git.use_remote_repo || false;
        document.getElementById('git-remote-url').value = config.git.remote_repo_url || '';
        document.getElementById('git-auto-create').checked = config.git.auto_create_repo || false;
    }
    
    // Agent settings
    if (config.agent) {
        document.getElementById('workspace-root').value = config.agent.workspace_root || '';
        document.getElementById('task-timeout').value = config.agent.task_timeout_seconds || '';
    }
    
    // Multi-agent workflow
    if (config.multi_agent_workflow) {
        if (config.multi_agent_workflow.planner) {
            document.getElementById('planner-enabled').checked = config.multi_agent_workflow.planner.enabled || false;
            document.getElementById('planner-turns').value = config.multi_agent_workflow.planner.max_turns || '';
        }
        if (config.multi_agent_workflow.worker) {
            document.getElementById('worker-enabled').checked = config.multi_agent_workflow.worker.enabled || false;
            document.getElementById('worker-turns').value = config.multi_agent_workflow.worker.max_turns || '';
        }
        if (config.multi_agent_workflow.evaluator) {
            document.getElementById('evaluator-enabled').checked = config.multi_agent_workflow.evaluator.enabled || false;
            document.getElementById('evaluator-turns').value = config.multi_agent_workflow.evaluator.max_turns || '';
        }
    }
    
    // Auto generation
    if (config.auto_generation) {
        document.getElementById('auto-gen-enabled').checked = config.auto_generation.enabled || false;
    }
}

// Collect form data into configuration object
function collectFormData() {
    const config = {
        claude_code: {
            binary_path: document.getElementById('claude-binary').value,
            model: document.getElementById('claude-model').value,
            threshold_day: parseFloat(document.getElementById('threshold-day').value) || 0,
            threshold_night: parseFloat(document.getElementById('threshold-night').value) || 0,
            night_start_hour: parseInt(document.getElementById('night-start').value) || 0,
            night_end_hour: parseInt(document.getElementById('night-end').value) || 0,
            // Preserve usage_command from existing config (not editable in UI)
            usage_command: currentConfig.claude_code?.usage_command || 'claude /usage'
        },
        git: {
            use_remote_repo: document.getElementById('git-use-remote').checked,
            remote_repo_url: document.getElementById('git-remote-url').value,
            auto_create_repo: document.getElementById('git-auto-create').checked
        },
        agent: {
            workspace_root: document.getElementById('workspace-root').value,
            task_timeout_seconds: parseInt(document.getElementById('task-timeout').value) || 1800
        },
        multi_agent_workflow: {
            planner: {
                enabled: document.getElementById('planner-enabled').checked,
                max_turns: parseInt(document.getElementById('planner-turns').value) || 1
            },
            worker: {
                enabled: document.getElementById('worker-enabled').checked,
                max_turns: parseInt(document.getElementById('worker-turns').value) || 1
            },
            evaluator: {
                enabled: document.getElementById('evaluator-enabled').checked,
                max_turns: parseInt(document.getElementById('evaluator-turns').value) || 1
            }
        },
        auto_generation: {
            enabled: document.getElementById('auto-gen-enabled').checked,
            prompts: currentConfig.auto_generation?.prompts || []
        }
    };
    
    return config;
}

// Save configuration to server
async function saveConfig() {
    const saveBtn = document.getElementById('save-btn');
    saveBtn.disabled = true;
    saveBtn.textContent = '💾 Saving...';
    
    try {
        const config = collectFormData();
        
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ config })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('✅ Configuration saved successfully! Restart daemon for changes to take effect.', 'success');
            currentConfig = config;
        } else {
            showMessage('❌ Error saving configuration: ' + data.error, 'error');
        }
    } catch (error) {
        showMessage('❌ Error saving configuration: ' + error.message, 'error');
    } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = '💾 Save Configuration';
    }
}

// Show message to user
function showMessage(text, type) {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = text;
    messageDiv.className = 'message ' + type;
    
    // Auto-hide success messages after 5 seconds
    if (type === 'success') {
        setTimeout(() => {
            messageDiv.className = 'message';
        }, 5000);
    }
}

// Initialize the page
document.addEventListener('DOMContentLoaded', () => {
    loadConfig();
    
    document.getElementById('save-btn').addEventListener('click', saveConfig);
    document.getElementById('reload-btn').addEventListener('click', () => {
        loadConfig();
        showMessage('Configuration reloaded', 'success');
    });
});
