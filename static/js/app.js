/**
 * Modern Plex Media Renamer JavaScript
 * Handles UI interactions, API calls, and dynamic content updates
 */

class PlexMediaRenamer {
    constructor() {
        this.currentTheme = localStorage.getItem('theme') || 'dark';
        this.discoveredFolders = [];
        this.scanResults = [];
        this.metadataIssues = [];
        this.isScanning = false;
        this.selectedFolders = new Set();

        this.init();
    }

    init() {
        this.setupTheme();
        this.setupEventListeners();
        this.loadConfiguration();
        this.startStatusPolling();
    }

    setupTheme() {
        document.documentElement.setAttribute('data-theme', this.currentTheme);
        this.updateThemeIcon();
    }

    updateThemeIcon() {
        const themeToggle = document.getElementById('themeToggle');
        const icon = themeToggle.querySelector('i');

        if (this.currentTheme === 'dark') {
            icon.className = 'bi bi-sun-fill';
            themeToggle.title = 'Switch to light mode';
        } else {
            icon.className = 'bi bi-moon-fill';
            themeToggle.title = 'Switch to dark mode';
        }
    }

    setupEventListeners() {
        // Theme toggle
        document.getElementById('themeToggle').addEventListener('click', () => {
            this.toggleTheme();
        });

        // Settings modal
        document.getElementById('settingsButton').addEventListener('click', () => {
            this.showSettings();
        });

        document.getElementById('closeSettings').addEventListener('click', () => {
            this.hideSettings();
        });

        document.getElementById('cancelSettings').addEventListener('click', () => {
            this.hideSettings();
        });

        document.getElementById('saveSettings').addEventListener('click', () => {
            this.saveSettings();
        });

        // Discovery
        document.getElementById('discoverButton').addEventListener('click', () => {
            this.discoverMediaFolders();
        });

        // Scanning
        document.getElementById('scanButton').addEventListener('click', () => {
            this.startScan();
        });

        document.getElementById('applyChangesButton').addEventListener('click', () => {
            this.applyChanges();
        });

        // Results table
        document.getElementById('selectAllButton').addEventListener('click', () => {
            this.selectAllResults();
        });

        document.getElementById('selectNoneButton').addEventListener('click', () => {
            this.selectNoneResults();
        });

        document.getElementById('selectAllCheckbox').addEventListener('change', (e) => {
            this.toggleAllResults(e.target.checked);
        });

        // Metadata issues
        document.getElementById('showMetadataIssues').addEventListener('click', () => {
            this.showMetadataIssues();
        });

        document.getElementById('closeMetadata').addEventListener('click', () => {
            this.hideMetadataIssues();
        });

        document.getElementById('closeMetadataButton').addEventListener('click', () => {
            this.hideMetadataIssues();
        });

        // Scan options
        document.getElementById('scanAllFolders').addEventListener('change', (e) => {
            this.togglePathGroup(!e.target.checked);
        });

        // Modal backdrop clicks
        document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
            backdrop.addEventListener('click', (e) => {
                if (e.target === backdrop) {
                    this.hideAllModals();
                }
            });
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideAllModals();
            }
        });
    }

    toggleTheme() {
        this.currentTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', this.currentTheme);
        document.documentElement.setAttribute('data-theme', this.currentTheme);
        this.updateThemeIcon();
    }

    togglePathGroup(show) {
        const pathGroup = document.getElementById('pathGroup');
        pathGroup.style.display = show ? 'block' : 'none';
    }

    async loadConfiguration() {
        try {
            const response = await fetch('/api/config');
            const data = await response.json();

            if (data.success) {
                this.populateSettings(data.config);
            }
        } catch (error) {
            console.error('Error loading configuration:', error);
        }
    }

    populateSettings(config) {
        document.getElementById('baseMediaPath').value = config.base_media_path || '';
        document.getElementById('moviesSubfolder').value = config.movies_path?.split('/').pop() || '';
        document.getElementById('tvShowsSubfolder').value = config.tv_shows_path?.split('/').pop() || '';
        document.getElementById('createMovieFolders').checked = config.create_movie_folders || false;
        document.getElementById('includeEpisodeTitle').checked = config.include_episode_title || false;
        document.getElementById('includeSeriesId').checked = config.include_series_id || false;
    }

    async discoverMediaFolders() {
        const plexPath = document.getElementById('plexPath').value;
        const discoverButton = document.getElementById('discoverButton');

        if (!plexPath.trim()) {
            this.showAlert('Please enter a valid Plex directory path', 'error');
            return;
        }

        try {
            discoverButton.disabled = true;
            discoverButton.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Discovering...';

            const response = await fetch('/api/discover-media-folders', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ base_path: plexPath })
            });

            const data = await response.json();

            if (data.success) {
                this.showAlert('Media folder discovery started', 'info');
            } else {
                this.showAlert(data.error || 'Failed to start discovery', 'error');
            }
        } catch (error) {
            console.error('Error starting discovery:', error);
            this.showAlert('Error starting discovery', 'error');
        } finally {
            discoverButton.disabled = false;
            discoverButton.innerHTML = '<i class="bi bi-search"></i> Discover Folders';
        }
    }

    async loadMediaFolders() {
        try {
            const response = await fetch('/api/media-folders');
            const data = await response.json();

            if (data.success) {
                this.discoveredFolders = data.folders;
                this.renderMediaFolders();
            }
        } catch (error) {
            console.error('Error loading media folders:', error);
        }
    }

    renderMediaFolders() {
        const grid = document.getElementById('mediaFoldersGrid');

        if (this.discoveredFolders.length === 0) {
            grid.style.display = 'none';
            return;
        }

        grid.style.display = 'grid';
        grid.innerHTML = '';

        this.discoveredFolders.forEach((folder, index) => {
            const card = this.createFolderCard(folder, index);
            grid.appendChild(card);
        });
    }

    createFolderCard(folder, index) {
        const card = document.createElement('div');
        card.className = 'media-folder-card fade-in';
        card.dataset.index = index;

        const typeClass = folder.detected_type || 'unknown';
        const confidencePercent = Math.round(folder.confidence_score * 100);

        card.innerHTML = `
            <div class="folder-header">
                <div>
                    <div class="folder-name">${folder.name}</div>
                    <div class="folder-type ${typeClass}">${folder.detected_type || 'Unknown'}</div>
                </div>
                <div class="confidence-score">${confidencePercent}%</div>
            </div>
            <div class="folder-stats">
                <span>${folder.media_file_count} media files</span>
                <span>${folder.subdirectory_count} subdirs</span>
            </div>
        `;

        card.addEventListener('click', () => {
            this.toggleFolderSelection(index, card);
        });

        return card;
    }

    toggleFolderSelection(index, card) {
        if (this.selectedFolders.has(index)) {
            this.selectedFolders.delete(index);
            card.classList.remove('selected');
        } else {
            this.selectedFolders.add(index);
            card.classList.add('selected');
        }
    }

    async startScan() {
        const mediaType = document.querySelector('input[name="mediaType"]:checked').value;
        const scanAllFolders = document.getElementById('scanAllFolders').checked;
        const customPath = document.getElementById('scanPath').value;
        const scanButton = document.getElementById('scanButton');

        try {
            scanButton.disabled = true;
            scanButton.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Scanning...';

            const requestData = {
                media_type: mediaType,
                scan_all_folders: scanAllFolders
            };

            if (!scanAllFolders && customPath.trim()) {
                requestData.scan_path = customPath.trim();
            }

            const response = await fetch('/api/scan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });

            const data = await response.json();

            if (data.success) {
                this.showAlert('Scan started successfully', 'info');
                this.isScanning = true;
                this.showProgress();
            } else {
                this.showAlert(data.error || 'Failed to start scan', 'error');
            }
        } catch (error) {
            console.error('Error starting scan:', error);
            this.showAlert('Error starting scan', 'error');
        } finally {
            scanButton.disabled = false;
            scanButton.innerHTML = '<i class="bi bi-search"></i> Scan Files';
        }
    }

    async applyChanges() {
        const selectedRows = document.querySelectorAll('#resultsTableBody input[type="checkbox"]:checked');
        const dryRun = document.getElementById('dryRunMode').checked;
        const applyButton = document.getElementById('applyChangesButton');

        if (selectedRows.length === 0) {
            this.showAlert('Please select files to rename', 'warning');
            return;
        }

        try {
            applyButton.disabled = true;
            applyButton.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Processing...';

            const selectedOperations = Array.from(selectedRows).map(checkbox =>
                parseInt(checkbox.dataset.index)
            );

            const response = await fetch('/api/rename', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    operations: selectedOperations,
                    dry_run: dryRun
                })
            });

            const data = await response.json();

            if (data.success) {
                const message = dryRun ?
                    `Dry run completed: ${data.summary.successful}/${data.summary.total} operations would succeed` :
                    `Rename completed: ${data.summary.successful}/${data.summary.total} files renamed successfully`;

                this.showAlert(message, data.summary.failed > 0 ? 'warning' : 'success');

                if (!dryRun) {
                    this.loadScanResults(); // Refresh results
                }
            } else {
                this.showAlert(data.error || 'Failed to apply changes', 'error');
            }
        } catch (error) {
            console.error('Error applying changes:', error);
            this.showAlert('Error applying changes', 'error');
        } finally {
            applyButton.disabled = false;
            applyButton.innerHTML = '<i class="bi bi-play-fill"></i> Apply Changes';
        }
    }

    async loadScanResults() {
        try {
            const response = await fetch('/api/scan/results');
            const data = await response.json();

            if (data.success) {
                this.scanResults = data.results;
                this.metadataIssues = data.metadata_issues || [];
                this.renderScanResults();
                this.updateMetadataIssuesCount();
            }
        } catch (error) {
            console.error('Error loading scan results:', error);
        }
    }

    renderScanResults() {
        const tableBody = document.getElementById('resultsTableBody');

        // Clear metadata issues for fresh tracking
        this.metadataIssues = [];

        if (this.scanResults.length === 0) {
            tableBody.innerHTML = `
                <tr class="empty-state">
                    <td colspan="6">
                        <div class="empty-content">
                            <i class="bi bi-inbox"></i>
                            <h3>No files scanned yet</h3>
                            <p>Start by discovering media folders or scanning a specific directory</p>
                        </div>
                    </td>
                </tr>
            `;
            return;
        }

        const rows = this.scanResults.map((result, index) => this.createResultRow(result, index));
        tableBody.innerHTML = rows.join('');

        // Update metadata issues count
        this.updateMetadataIssuesCount();

        // Add event listeners to checkboxes
        document.querySelectorAll('.result-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                this.updateApplyButton();
            });
        });

        // Enable apply button if there are valid operations
        this.updateApplyButton();
    }

    createResultRow(result, index) {
        const metadataStatus = this.getMetadataStatusText(result.metadata_status || 'unknown');
        const hasMetadataIssue = ['not_found', 'error', 'api_unavailable', 'partial'].includes(result.metadata_status);

        if (hasMetadataIssue) {
            this.metadataIssues.push({
                file: result.source_path || result.filename,
                message: result.error_message || 'Unknown metadata issue',
                status: result.metadata_status
            });
        }

        return `
            <tr data-index="${index}" class="${hasMetadataIssue ? 'metadata-issue' : ''}">
                <td class="checkbox-column">
                    <label class="checkbox-option">
                        <input type="checkbox" class="result-checkbox" data-index="${index}">
                        <span class="checkbox-custom"></span>
                    </label>
                </td>
                <td>
                    <div class="file-info">
                        <div class="filename">${result.filename || 'Unknown'}</div>
                        <div class="filepath">${result.source_path || ''}</div>
                    </div>
                </td>
                <td>
                    <div class="new-filename">
                        ${result.target_path ? result.target_path.split('/').pop() : 'No changes'}
                    </div>
                </td>
                <td>
                    <span class="media-type ${result.media_type || 'unknown'}">
                        <i class="bi bi-${result.media_type === 'movie' ? 'camera-reels' : result.media_type === 'tv' ? 'tv' : 'question-circle'}"></i>
                        ${result.media_type === 'movie' ? 'Movie' : result.media_type === 'tv' ? 'TV Show' : 'Unknown'}
                    </span>
                </td>
                <td>
                    <span class="metadata-status ${result.metadata_status || 'unknown'}" 
                          title="${result.error_message || ''}">
                        ${metadataStatus}
                    </span>
                </td>
                <td>
                    <button class="btn btn-ghost btn-sm" onclick="app.showFileDetails(${index})" title="View details">
                        <i class="bi bi-info-circle"></i>
                    </button>
                </td>
            </tr>
        `;
    }

    getMetadataStatusText(status) {
        const statusMap = {
            'found': 'Found',
            'not_found': 'Not Found',
            'partial': 'Partial',
            'error': 'Error',
            'api_unavailable': 'API Unavailable',
            'unknown': 'Unknown'
        };
        return statusMap[status] || 'Unknown';
    }

    updateApplyButton() {
        const checkboxes = document.querySelectorAll('.result-checkbox:checked');
        const applyButton = document.getElementById('applyChangesButton');
        applyButton.disabled = checkboxes.length === 0;
    }

    selectAllResults() {
        const checkboxes = document.querySelectorAll('.result-checkbox');
        const selectAllCheckbox = document.getElementById('selectAllCheckbox');

        checkboxes.forEach(checkbox => {
            checkbox.checked = true;
        });
        selectAllCheckbox.checked = true;
        this.updateApplyButton();
    }

    selectNoneResults() {
        const checkboxes = document.querySelectorAll('.result-checkbox');
        const selectAllCheckbox = document.getElementById('selectAllCheckbox');

        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        selectAllCheckbox.checked = false;
        this.updateApplyButton();
    }

    toggleAllResults(checked) {
        const checkboxes = document.querySelectorAll('.result-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = checked;
        });
        this.updateApplyButton();
    }

    updateMetadataIssuesCount() {
        const issuesCount = this.metadataIssues.length;
        const metadataIssuesElement = document.getElementById('metadataIssues');
        const showIssuesButton = document.getElementById('showMetadataIssues');

        if (metadataIssuesElement) {
            metadataIssuesElement.textContent = issuesCount;
        }

        if (showIssuesButton) {
            showIssuesButton.style.display = issuesCount > 0 ? 'flex' : 'none';
        }
    }

    showMetadataIssues() {
        if (this.metadataIssues.length === 0) {
            this.showAlert('No metadata issues found', 'info');
            return;
        }

        const modal = document.getElementById('metadataModal');
        const issuesList = document.getElementById('issuesList');

        issuesList.innerHTML = this.metadataIssues.map(issue => `
            <div class="issue-item">
                <div class="issue-file">${issue.file}</div>
                <div class="issue-message">
                    <span class="metadata-status ${issue.status}">${this.getMetadataStatusText(issue.status)}</span>
                    ${issue.message}
                </div>
            </div>
        `).join('');

        modal.classList.add('show');
    }

    hideMetadataIssues() {
        document.getElementById('metadataModal').classList.remove('show');
    }

    showSettings() {
        document.getElementById('settingsModal').classList.add('show');
    }

    hideSettings() {
        document.getElementById('settingsModal').classList.remove('show');
    }

    hideAllModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.remove('show');
        });
    }

    async saveSettings() {
        const settings = {
            tmdb_api_key: document.getElementById('tmdbApiKey').value,
            tvdb_api_key: document.getElementById('tvdbApiKey').value,
            base_media_path: document.getElementById('baseMediaPath').value,
            movies_subfolder: document.getElementById('moviesSubfolder').value,
            tv_shows_subfolder: document.getElementById('tvShowsSubfolder').value,
            create_movie_folders: document.getElementById('createMovieFolders').checked,
            include_episode_title: document.getElementById('includeEpisodeTitle').checked,
            include_series_id: document.getElementById('includeSeriesId').checked
        };

        try {
            const response = await fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            });

            const data = await response.json();

            if (data.success) {
                this.showAlert('Settings saved successfully', 'success');
                this.hideSettings();
            } else {
                this.showAlert(data.error || 'Failed to save settings', 'error');
            }
        } catch (error) {
            console.error('Error saving settings:', error);
            this.showAlert('Error saving settings', 'error');
        }
    }

    showProgress() {
        document.getElementById('progressContainer').style.display = 'block';
    }

    hideProgress() {
        document.getElementById('progressContainer').style.display = 'none';
    }

    updateProgress(progress, message) {
        document.getElementById('progressBar').style.width = `${progress}%`;
        document.getElementById('progressText').textContent = message;
    }

    updateStats(filesFound, operationsReady) {
        document.getElementById('filesFound').textContent = filesFound;
        document.getElementById('operationsReady').textContent = operationsReady;
    }

    async startStatusPolling() {
        setInterval(async () => {
            try {
                const response = await fetch('/api/scan/status');
                const data = await response.json();

                if (data.success) {
                    const status = data.status;

                    if (status.is_scanning) {
                        this.showProgress();
                        this.updateProgress(status.progress, status.message);
                    } else {
                        if (this.isScanning) {
                            // Scan just finished
                            this.isScanning = false;
                            this.hideProgress();
                            this.loadScanResults();
                            this.loadMediaFolders();
                        }
                    }

                    this.updateStats(data.files_count, data.operations_count);
                }
            } catch (error) {
                console.error('Error polling status:', error);
            }
        }, 1000);
    }

    showAlert(message, type = 'info') {
        const alertContainer = document.getElementById('alertContainer');
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} fade-in`;

        const iconMap = {
            success: 'bi-check-circle-fill',
            error: 'bi-exclamation-triangle-fill',
            warning: 'bi-exclamation-triangle-fill',
            info: 'bi-info-circle-fill'
        };

        alert.innerHTML = `
            <i class="bi ${iconMap[type] || iconMap.info}"></i>
            <span>${message}</span>
        `;

        alertContainer.appendChild(alert);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }

    showFileDetails(index) {
        const result = this.scanResults[index];
        if (!result) return;

        // Create a simple details display
        const details = `
            File: ${result.filename}
            Source: ${result.source_path}
            Target: ${result.target_path}
            Metadata Status: ${this.getMetadataStatusText(result.metadata_status)}
            ${result.metadata_message ? 'Message: ' + result.metadata_message : ''}
        `;

        alert(details); // Simple alert for now, could be enhanced with a proper modal
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new PlexMediaRenamer();
});

// Add some utility functions for enhanced UX
document.addEventListener('DOMContentLoaded', () => {
    // Add loading states to buttons
    document.querySelectorAll('.btn').forEach(button => {
        button.addEventListener('click', function () {
            if (!this.disabled) {
                this.classList.add('loading');
                setTimeout(() => {
                    this.classList.remove('loading');
                }, 2000);
            }
        });
    });

    // Add smooth scrolling for internal links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add intersection observer for animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
            }
        });
    }, observerOptions);

    // Observe elements that should animate in
    document.querySelectorAll('.section, .stat-card, .media-folder-card').forEach(el => {
        observer.observe(el);
    });
}); 