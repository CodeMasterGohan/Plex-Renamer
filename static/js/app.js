// Plex Media Renamer Web Application
// Main JavaScript functionality

class PlexRenamerApp {
    constructor() {
        this.config = {};
        this.scanResults = [];
        this.selectedFiles = new Set();
        this.currentScanStatus = null;
        this.scanInterval = null;
        this.currentTheme = localStorage.getItem('theme') || 'light';
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupTheme();
        this.loadConfig();
        this.updateMediaTypeDisplay();
    }

    // Event Listeners Setup
    setupEventListeners() {
        // Media type radio buttons
        document.querySelectorAll('input[name="mediaType"]').forEach(radio => {
            radio.addEventListener('change', () => this.updateMediaTypeDisplay());
        });

        // Control buttons
        document.getElementById('scanButton').addEventListener('click', () => this.startScan());
        document.getElementById('applyChangesButton').addEventListener('click', () => this.applyChanges());
        document.getElementById('browsePath').addEventListener('click', () => this.showDirectoryBrowser());

        // Selection buttons
        document.getElementById('selectAllButton').addEventListener('click', () => this.selectAllFiles());
        document.getElementById('selectNoneButton').addEventListener('click', () => this.selectNoFiles());
        document.getElementById('previewButton').addEventListener('click', () => this.showPreview());

        // Settings
        document.getElementById('saveSettingsButton').addEventListener('click', () => this.saveSettings());

        // Theme toggle
        document.getElementById('themeToggle').addEventListener('click', () => this.toggleTheme());

        // Master checkbox
        document.getElementById('selectAllCheckbox').addEventListener('change', (e) => {
            if (e.target.checked) {
                this.selectAllFiles();
            } else {
                this.selectNoFiles();
            }
        });

        // Directory browser
        document.getElementById('selectPathButton').addEventListener('click', () => this.selectBrowserPath());
        document.getElementById('parentDirButton').addEventListener('click', () => this.browseParentDirectory());

        // Dry run mode
        document.getElementById('dryRunMode').addEventListener('change', (e) => {
            this.updateApplyButtonText();
        });
    }

    // Theme Management
    setupTheme() {
        document.documentElement.setAttribute('data-bs-theme', this.currentTheme);
        this.updateThemeButton();
    }

    toggleTheme() {
        this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-bs-theme', this.currentTheme);
        localStorage.setItem('theme', this.currentTheme);
        this.updateThemeButton();
    }

    updateThemeButton() {
        const themeButton = document.getElementById('themeToggle');
        const icon = themeButton.querySelector('i');
        if (this.currentTheme === 'dark') {
            icon.className = 'bi bi-sun-fill';
        } else {
            icon.className = 'bi bi-moon-fill';
        }
    }

    // Configuration Management
    async loadConfig() {
        try {
            const response = await fetch('/api/config');
            const data = await response.json();
            
            if (data.success) {
                this.config = data.config;
                this.updateConfigUI();
                this.updateMediaTypeDisplay();
            } else {
                this.showAlert('Error loading configuration: ' + data.error, 'danger');
            }
        } catch (error) {
            this.showAlert('Failed to load configuration: ' + error.message, 'danger');
        }
    }

    updateConfigUI() {
        // Update settings form
        document.getElementById('baseMediaPath').value = this.config.base_media_path || '';
        document.getElementById('moviesSubfolder').value = this.config.movies_path ? 
            this.config.movies_path.split('/').pop() : 'movies';
        document.getElementById('tvShowsSubfolder').value = this.config.tv_shows_path ? 
            this.config.tv_shows_path.split('/').pop() : 'tv_shows';
        document.getElementById('preferredLanguage').value = this.config.preferred_language || 'en-US';
        document.getElementById('createMovieFolders').checked = this.config.create_movie_folders;
        document.getElementById('includeEpisodeTitle').checked = this.config.include_episode_title;
        document.getElementById('includeSeriesId').checked = this.config.include_series_id;
        document.getElementById('preferredIdSource').value = this.config.preferred_id_source || 'tvdb';
        document.getElementById('dryRunMode').checked = this.config.dry_run_mode;
    }

    async saveSettings() {
        try {
            const formData = {
                tmdb_api_key: document.getElementById('tmdbApiKey').value,
                tvdb_api_key: document.getElementById('tvdbApiKey').value,
                base_media_path: document.getElementById('baseMediaPath').value,
                movies_subfolder: document.getElementById('moviesSubfolder').value,
                tv_shows_subfolder: document.getElementById('tvShowsSubfolder').value,
                preferred_language: document.getElementById('preferredLanguage').value,
                dry_run_mode: document.getElementById('dryRunMode').checked,
                create_movie_folders: document.getElementById('createMovieFolders').checked,
                include_episode_title: document.getElementById('includeEpisodeTitle').checked,
                include_series_id: document.getElementById('includeSeriesId').checked,
                preferred_id_source: document.getElementById('preferredIdSource').value
            };

            const response = await fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();
            
            if (data.success) {
                this.showAlert('Settings saved successfully!', 'success');
                bootstrap.Modal.getInstance(document.getElementById('settingsModal')).hide();
                await this.loadConfig(); // Reload config
            } else {
                this.showAlert('Error saving settings: ' + data.error, 'danger');
            }
        } catch (error) {
            this.showAlert('Failed to save settings: ' + error.message, 'danger');
        }
    }

    // Media Type Management
    updateMediaTypeDisplay() {
        const mediaType = document.querySelector('input[name="mediaType"]:checked').value;
        const pathInput = document.getElementById('scanPath');
        
        if (mediaType === 'movies' && this.config.movies_path) {
            pathInput.value = this.config.movies_path;
        } else if (mediaType === 'tv_shows' && this.config.tv_shows_path) {
            pathInput.value = this.config.tv_shows_path;
        } else {
            pathInput.value = 'Not configured';
        }
    }

    // File Scanning
    async startScan() {
        const mediaType = document.querySelector('input[name="mediaType"]:checked').value;
        const scanPath = document.getElementById('scanPath').value;
        
        if (!scanPath || scanPath === 'Not configured') {
            this.showAlert('Please configure media paths in Settings first.', 'warning');
            return;
        }

        try {
            // Disable scan button and show progress
            document.getElementById('scanButton').disabled = true;
            document.getElementById('scanButton').innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Scanning...';
            this.showProgress(0, 'Starting scan...');

            const response = await fetch('/api/scan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    media_type: mediaType,
                    scan_path: scanPath
                })
            });

            const data = await response.json();
            
            if (data.success) {
                // Start polling for scan status
                this.startScanStatusPolling();
            } else {
                this.showAlert('Error starting scan: ' + data.error, 'danger');
                this.resetScanButton();
            }
        } catch (error) {
            this.showAlert('Failed to start scan: ' + error.message, 'danger');
            this.resetScanButton();
        }
    }

    startScanStatusPolling() {
        this.scanInterval = setInterval(async () => {
            try {
                const response = await fetch('/api/scan/status');
                const data = await response.json();
                
                if (data.success) {
                    const status = data.status;
                    this.updateProgress(status.progress, status.message);
                    this.updateStatistics(data.files_count, data.operations_count);

                    if (!status.is_scanning) {
                        // Scan completed
                        clearInterval(this.scanInterval);
                        this.scanInterval = null;
                        this.resetScanButton();
                        this.hideProgress();
                        await this.loadScanResults();
                    }
                }
            } catch (error) {
                console.error('Error polling scan status:', error);
            }
        }, 1000);
    }

    async loadScanResults() {
        try {
            const response = await fetch('/api/scan/results');
            const data = await response.json();
            
            if (data.success) {
                this.scanResults = data.results;
                this.displayScanResults();
                this.updateButtonStates();
            } else {
                this.showAlert('Error loading scan results: ' + data.error, 'danger');
            }
        } catch (error) {
            this.showAlert('Failed to load scan results: ' + error.message, 'danger');
        }
    }

    displayScanResults() {
        const tbody = document.getElementById('resultsTableBody');
        
        if (this.scanResults.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center text-muted py-5">
                        <i class="bi bi-inbox display-4 d-block mb-2"></i>
                        No files found to rename.
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = this.scanResults.map((result, index) => `
            <tr>
                <td>
                    <input type="checkbox" class="form-check-input file-checkbox" 
                           data-index="${index}" ${this.selectedFiles.has(index) ? 'checked' : ''}>
                </td>
                <td>
                    <div class="file-path">${this.truncatePath(result.filename)}</div>
                    <small class="text-muted">${this.truncatePath(result.source_path, 50)}</small>
                </td>
                <td>
                    <div class="fw-bold">${result.new_filename}</div>
                    <small class="text-muted">${this.truncatePath(result.target_path, 50)}</small>
                </td>
                <td>
                    <span class="status-badge status-${result.status.toLowerCase()}">${result.status}</span>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-info" onclick="app.showFileDetails(${index})">
                        <i class="bi bi-info-circle"></i>
                    </button>
                </td>
            </tr>
        `).join('');

        // Add event listeners to checkboxes
        document.querySelectorAll('.file-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const index = parseInt(e.target.dataset.index);
                if (e.target.checked) {
                    this.selectedFiles.add(index);
                } else {
                    this.selectedFiles.delete(index);
                }
                this.updateButtonStates();
                this.updateMasterCheckbox();
            });
        });
    }

    // File Selection Management
    selectAllFiles() {
        this.selectedFiles.clear();
        this.scanResults.forEach((_, index) => this.selectedFiles.add(index));
        document.querySelectorAll('.file-checkbox').forEach(cb => cb.checked = true);
        document.getElementById('selectAllCheckbox').checked = true;
        this.updateButtonStates();
    }

    selectNoFiles() {
        this.selectedFiles.clear();
        document.querySelectorAll('.file-checkbox').forEach(cb => cb.checked = false);
        document.getElementById('selectAllCheckbox').checked = false;
        this.updateButtonStates();
    }

    updateMasterCheckbox() {
        const masterCheckbox = document.getElementById('selectAllCheckbox');
        const totalFiles = this.scanResults.length;
        const selectedCount = this.selectedFiles.size;
        
        if (selectedCount === 0) {
            masterCheckbox.checked = false;
            masterCheckbox.indeterminate = false;
        } else if (selectedCount === totalFiles) {
            masterCheckbox.checked = true;
            masterCheckbox.indeterminate = false;
        } else {
            masterCheckbox.checked = false;
            masterCheckbox.indeterminate = true;
        }
    }

    // Apply Changes
    async applyChanges() {
        if (this.selectedFiles.size === 0) {
            this.showAlert('Please select files to process.', 'warning');
            return;
        }

        const dryRun = document.getElementById('dryRunMode').checked;
        const selectedOperations = Array.from(this.selectedFiles);

        try {
            document.getElementById('applyChangesButton').disabled = true;
            document.getElementById('applyChangesButton').innerHTML = 
                '<i class="bi bi-hourglass-split me-2"></i>Processing...';

            const response = await fetch('/api/rename', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    dry_run: dryRun,
                    operations: selectedOperations
                })
            });

            const data = await response.json();
            
            if (data.success) {
                const summary = data.summary;
                const message = dryRun 
                    ? `Dry run completed: ${summary.total} operations would be performed.`
                    : `Applied ${summary.successful} operations successfully. ${summary.failed} failed.`;
                
                this.showAlert(message, summary.failed > 0 ? 'warning' : 'success');
                
                if (!dryRun && summary.successful > 0) {
                    // Refresh scan results after successful rename
                    await this.loadScanResults();
                }
            } else {
                this.showAlert('Error applying changes: ' + data.error, 'danger');
            }
        } catch (error) {
            this.showAlert('Failed to apply changes: ' + error.message, 'danger');
        } finally {
            document.getElementById('applyChangesButton').disabled = false;
            this.updateApplyButtonText();
        }
    }

    // Directory Browser
    async showDirectoryBrowser() {
        const currentPath = document.getElementById('scanPath').value;
        const startPath = currentPath !== 'Not configured' ? currentPath : '/media/plex';
        
        await this.browseDirectory(startPath);
        new bootstrap.Modal(document.getElementById('browserModal')).show();
    }

    async browseDirectory(path) {
        try {
            const response = await fetch('/api/browse', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ path: path })
            });

            const data = await response.json();
            
            if (data.success) {
                this.displayDirectoryContents(data);
            } else {
                this.showAlert('Error browsing directory: ' + data.error, 'danger');
            }
        } catch (error) {
            this.showAlert('Failed to browse directory: ' + error.message, 'danger');
        }
    }

    displayDirectoryContents(data) {
        document.getElementById('currentPath').value = data.path;
        document.getElementById('selectPathButton').disabled = false;
        
        const tbody = document.getElementById('browserTableBody');
        const items = [...data.directories, ...data.files];
        
        tbody.innerHTML = items.map(item => `
            <tr ${item.type === 'directory' ? 'style="cursor: pointer;" onclick="app.browseDirectory(\'' + item.path + '\')"' : ''}>
                <td>
                    <i class="bi bi-${item.type === 'directory' ? 'folder' : 'file-earmark'} me-2"></i>
                    ${item.name}
                </td>
                <td>
                    <span class="badge bg-${item.type === 'directory' ? 'primary' : 'secondary'}">
                        ${item.type}
                    </span>
                </td>
                <td>
                    ${item.type === 'directory' ? 
                        '<button class="btn btn-sm btn-outline-primary" onclick="app.browseDirectory(\'' + item.path + '\')"><i class="bi bi-folder-plus"></i></button>' : 
                        '-'
                    }
                </td>
            </tr>
        `).join('');
    }

    async browseParentDirectory() {
        const currentPath = document.getElementById('currentPath').value;
        const parentPath = currentPath.split('/').slice(0, -1).join('/') || '/';
        await this.browseDirectory(parentPath);
    }

    selectBrowserPath() {
        const selectedPath = document.getElementById('currentPath').value;
        document.getElementById('scanPath').value = selectedPath;
        bootstrap.Modal.getInstance(document.getElementById('browserModal')).hide();
    }

    // Preview
    showPreview() {
        if (this.selectedFiles.size === 0) {
            this.showAlert('Please select files to preview.', 'warning');
            return;
        }

        const selectedResults = Array.from(this.selectedFiles).map(index => this.scanResults[index]);
        const previewContent = document.getElementById('previewContent');
        
        previewContent.innerHTML = `
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Current Path</th>
                            <th>New Path</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${selectedResults.map(result => `
                            <tr>
                                <td class="file-path">${result.source_path}</td>
                                <td class="file-path">${result.target_path}</td>
                                <td>
                                    <span class="badge bg-primary">
                                        ${result.source_path === result.target_path ? 'No Change' : 'Rename'}
                                    </span>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

        new bootstrap.Modal(document.getElementById('previewModal')).show();
    }

    // UI Helper Methods
    resetScanButton() {
        document.getElementById('scanButton').disabled = false;
        document.getElementById('scanButton').innerHTML = '<i class="bi bi-search me-2"></i>Scan Files';
    }

    showProgress(progress, message) {
        document.getElementById('progressContainer').style.display = 'block';
        document.getElementById('progressBar').style.width = progress + '%';
        document.getElementById('progressText').textContent = message;
    }

    updateProgress(progress, message) {
        document.getElementById('progressBar').style.width = progress + '%';
        document.getElementById('progressText').textContent = message;
    }

    hideProgress() {
        document.getElementById('progressContainer').style.display = 'none';
    }

    updateStatistics(filesFound, operationsReady) {
        document.getElementById('filesFound').textContent = filesFound;
        document.getElementById('operationsReady').textContent = operationsReady;
    }

    updateButtonStates() {
        const hasSelection = this.selectedFiles.size > 0;
        const hasResults = this.scanResults.length > 0;
        
        document.getElementById('applyChangesButton').disabled = !hasSelection;
        document.getElementById('previewButton').disabled = !hasSelection;
        document.getElementById('selectAllButton').disabled = !hasResults;
        document.getElementById('selectNoneButton').disabled = !hasResults;
    }

    updateApplyButtonText() {
        const button = document.getElementById('applyChangesButton');
        const dryRun = document.getElementById('dryRunMode').checked;
        button.innerHTML = dryRun 
            ? '<i class="bi bi-eye me-2"></i>Preview Changes'
            : '<i class="bi bi-play-fill me-2"></i>Apply Changes';
    }

    showAlert(message, type = 'info') {
        const alertContainer = document.getElementById('alertContainer');
        const alertId = 'alert-' + Date.now();
        
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" id="${alertId}" role="alert">
                <i class="bi bi-${this.getAlertIcon(type)} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        alertContainer.insertAdjacentHTML('beforeend', alertHtml);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alert = document.getElementById(alertId);
            if (alert) {
                bootstrap.Alert.getOrCreateInstance(alert).close();
            }
        }, 5000);
    }

    getAlertIcon(type) {
        const icons = {
            success: 'check-circle-fill',
            danger: 'exclamation-triangle-fill',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    truncatePath(path, maxLength = 40) {
        if (path.length <= maxLength) return path;
        return '...' + path.slice(-(maxLength - 3));
    }

    showFileDetails(index) {
        const result = this.scanResults[index];
        const metadata = result.metadata;
        
        let detailsHtml = `
            <h6>File Details</h6>
            <p><strong>Original:</strong> ${result.source_path}</p>
            <p><strong>New:</strong> ${result.target_path}</p>
        `;
        
        if (metadata && metadata.media_info) {
            const media = metadata.media_info;
            detailsHtml += `
                <h6>Media Information</h6>
                <p><strong>Title:</strong> ${media.title}</p>
                ${media.year ? `<p><strong>Year:</strong> ${media.year}</p>` : ''}
                ${media.season ? `<p><strong>Season:</strong> ${media.season}</p>` : ''}
                ${media.episode ? `<p><strong>Episode:</strong> ${media.episode}</p>` : ''}
            `;
        }
        
        // Create and show modal
        const modalHtml = `
            <div class="modal fade" id="fileDetailsModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">File Details</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">${detailsHtml}</div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        const existing = document.getElementById('fileDetailsModal');
        if (existing) existing.remove();
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        new bootstrap.Modal(document.getElementById('fileDetailsModal')).show();
    }
}

// Initialize the application
const app = new PlexRenamerApp(); 