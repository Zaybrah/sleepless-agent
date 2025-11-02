// File browser management for Sleepless Agent

let currentPath = "";
let newItemType = "file"; // "file" or "folder"

// Constants
const EDITOR_OPEN_DELAY_MS = 500; // Delay before opening editor after file creation to allow UI to update

// Load file list
async function loadFiles(path = "") {
    const fileList = document.getElementById('file-list');
    fileList.innerHTML = '<div class="loading">Loading...</div>';
    
    try {
        const response = await fetch(`/api/files/browse?path=${encodeURIComponent(path)}`);
        const data = await response.json();
        
        if (data.success) {
            currentPath = path;
            updateBreadcrumb(path);
            renderFileList(data);
        } else {
            showMessage('Error loading files: ' + data.error, 'error');
            fileList.innerHTML = '<div class="empty-folder">Error loading files</div>';
        }
    } catch (error) {
        showMessage('Error loading files: ' + error.message, 'error');
        fileList.innerHTML = '<div class="empty-folder">Error loading files</div>';
    }
}

// Render file list
function renderFileList(data) {
    const fileList = document.getElementById('file-list');
    
    if (data.type === 'directory' && data.items.length === 0) {
        fileList.innerHTML = `
            <div class="empty-folder">
                <div class="empty-folder-icon">📂</div>
                <p>This folder is empty</p>
            </div>
        `;
        return;
    }
    
    fileList.innerHTML = '';
    
    // Add parent directory link if not at root
    if (currentPath) {
        const parentPath = currentPath.split('/').slice(0, -1).join('/');
        const parentItem = createFileItem({
            name: '..',
            path: parentPath,
            type: 'directory'
        }, true);
        fileList.appendChild(parentItem);
    }
    
    // Add items
    if (data.items) {
        // Sort: directories first, then files
        const sorted = data.items.sort((a, b) => {
            if (a.type === b.type) {
                return a.name.localeCompare(b.name);
            }
            return a.type === 'directory' ? -1 : 1;
        });
        
        sorted.forEach(item => {
            const element = createFileItem(item);
            fileList.appendChild(element);
        });
    }
}

// Create file item element
function createFileItem(item, isParent = false) {
    const div = document.createElement('div');
    div.className = 'file-item';
    
    const icon = item.type === 'directory' ? '📁' : '📄';
    const sizeText = item.size !== undefined ? formatFileSize(item.size) : '';
    
    div.innerHTML = `
        <div class="file-info">
            <span class="file-icon">${icon}</span>
            <span class="file-name">${item.name}</span>
            ${sizeText ? `<span class="file-size">${sizeText}</span>` : ''}
        </div>
        ${!isParent ? `
            <div class="file-actions">
                ${item.type === 'file' ? '<button class="action-btn edit" onclick="editFile(\'' + item.path + '\')">✏️ Edit</button>' : ''}
                <button class="action-btn delete" onclick="deleteItem(\'' + item.path + '\', \'' + item.type + '\')">🗑️ Delete</button>
            </div>
        ` : ''}
    `;
    
    if (item.type === 'directory') {
        div.style.cursor = 'pointer';
        div.addEventListener('click', (e) => {
            // Don't navigate if clicking action buttons
            if (!e.target.closest('.file-actions')) {
                loadFiles(item.path);
            }
        });
    }
    
    return div;
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Update breadcrumb navigation
function updateBreadcrumb(path) {
    const container = document.getElementById('breadcrumb-container');
    const parts = path ? path.split('/') : [];
    
    let html = '<a href="#" data-path="" class="breadcrumb-item">workspace</a>';
    
    let currentPathParts = [];
    parts.forEach((part, index) => {
        if (part) {
            currentPathParts.push(part);
            const fullPath = currentPathParts.join('/');
            html += '<span class="breadcrumb-separator">/</span>';
            html += `<a href="#" data-path="${fullPath}" class="breadcrumb-item">${part}</a>`;
        }
    });
    
    container.innerHTML = html;
    
    // Add click handlers
    container.querySelectorAll('.breadcrumb-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const path = e.target.dataset.path;
            loadFiles(path);
        });
    });
}

// Edit file
async function editFile(path) {
    try {
        const response = await fetch(`/api/files/read?path=${encodeURIComponent(path)}`);
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('editor-title').textContent = `Edit: ${path.split('/').pop()}`;
            document.getElementById('file-editor').value = data.content;
            document.getElementById('file-editor').dataset.path = path;
            showModal('editor-modal');
        } else {
            showMessage('Error loading file: ' + data.error, 'error');
        }
    } catch (error) {
        showMessage('Error loading file: ' + error.message, 'error');
    }
}

// Save file
async function saveFile() {
    const path = document.getElementById('file-editor').dataset.path;
    const content = document.getElementById('file-editor').value;
    const saveBtn = document.getElementById('save-file-btn');
    
    saveBtn.disabled = true;
    saveBtn.textContent = '💾 Saving...';
    
    try {
        const response = await fetch('/api/files/write', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ path, content })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('✅ File saved successfully', 'success');
            hideModal('editor-modal');
            loadFiles(currentPath);
        } else {
            showMessage('❌ Error saving file: ' + data.error, 'error');
        }
    } catch (error) {
        showMessage('❌ Error saving file: ' + error.message, 'error');
    } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = '💾 Save';
    }
}

// Create new file
function newFile() {
    newItemType = 'file';
    document.getElementById('new-item-title').textContent = 'Create New File';
    document.getElementById('new-item-name').value = '';
    document.getElementById('new-item-name').placeholder = 'Enter file name...';
    showModal('new-item-modal');
}

// Create new folder
function newFolder() {
    newItemType = 'folder';
    document.getElementById('new-item-title').textContent = 'Create New Folder';
    document.getElementById('new-item-name').value = '';
    document.getElementById('new-item-name').placeholder = 'Enter folder name...';
    showModal('new-item-modal');
}

// Create item (file or folder)
async function createItem() {
    const name = document.getElementById('new-item-name').value.trim();
    
    if (!name) {
        showMessage('❌ Name is required', 'error');
        return;
    }
    
    const createBtn = document.getElementById('create-item-btn');
    createBtn.disabled = true;
    createBtn.textContent = 'Creating...';
    
    try {
        const path = currentPath ? `${currentPath}/${name}` : name;
        
        if (newItemType === 'folder') {
            // Create folder
            const response = await fetch('/api/files/create-folder', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ path })
            });
            
            const data = await response.json();
            
            if (data.success) {
                showMessage('✅ Folder created successfully', 'success');
                hideModal('new-item-modal');
                loadFiles(currentPath);
            } else {
                showMessage('❌ Error creating folder: ' + data.error, 'error');
            }
        } else {
            // Create empty file
            const response = await fetch('/api/files/write', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ path, content: '' })
            });
            
            const data = await response.json();
            
            if (data.success) {
                showMessage('✅ File created successfully', 'success');
                hideModal('new-item-modal');
                loadFiles(currentPath);
                // Open the new file for editing after a brief delay to allow the file list to update
                setTimeout(() => editFile(path), EDITOR_OPEN_DELAY_MS);
            } else {
                showMessage('❌ Error creating file: ' + data.error, 'error');
            }
        }
    } catch (error) {
        showMessage('❌ Error: ' + error.message, 'error');
    } finally {
        createBtn.disabled = false;
        createBtn.textContent = 'Create';
    }
}

// Delete file or folder
async function deleteItem(path, type) {
    const itemType = type === 'directory' ? 'folder' : 'file';
    const itemName = path.split('/').pop();
    
    if (!confirm(`Are you sure you want to delete this ${itemType}: ${itemName}?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/files/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ path })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(`✅ ${itemType.charAt(0).toUpperCase() + itemType.slice(1)} deleted successfully`, 'success');
            loadFiles(currentPath);
        } else {
            showMessage('❌ Error deleting ' + itemType + ': ' + data.error, 'error');
        }
    } catch (error) {
        showMessage('❌ Error deleting ' + itemType + ': ' + error.message, 'error');
    }
}

// Show modal
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.classList.add('show');
}

// Hide modal
function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.classList.remove('show');
}

// Show message
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

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadFiles();
    
    // Toolbar buttons
    document.getElementById('new-file-btn').addEventListener('click', newFile);
    document.getElementById('new-folder-btn').addEventListener('click', newFolder);
    document.getElementById('refresh-btn').addEventListener('click', () => loadFiles(currentPath));
    
    // Editor modal buttons
    document.getElementById('save-file-btn').addEventListener('click', saveFile);
    document.getElementById('close-editor-btn').addEventListener('click', () => hideModal('editor-modal'));
    document.getElementById('cancel-editor-btn').addEventListener('click', () => hideModal('editor-modal'));
    
    // New item modal buttons
    document.getElementById('create-item-btn').addEventListener('click', createItem);
    document.getElementById('close-new-item-btn').addEventListener('click', () => hideModal('new-item-modal'));
    document.getElementById('cancel-new-item-btn').addEventListener('click', () => hideModal('new-item-modal'));
    
    // Handle Enter key in new item input
    document.getElementById('new-item-name').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            createItem();
        }
    });
    
    // Close modal on background click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('show');
            }
        });
    });
});
