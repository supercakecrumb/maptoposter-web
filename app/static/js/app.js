/**
 * Alpine.js components for City Map Poster Generator
 */

// Quick Create Component (Home page)
function quickCreate() {
    return {
        form: {
            location: '',
            theme: 'noir',
            distance: 29000,
            latitude: null,
            longitude: null
        },
        suggestions: [],
        showSuggestions: false,
        searchTimeout: null,
        loading: false,
        error: null,
        
        searchLocation() {
            // Clear previous timeout
            if (this.searchTimeout) {
                clearTimeout(this.searchTimeout);
            }
            
            // Debounce search
            this.searchTimeout = setTimeout(async () => {
                if (this.form.location.length < 3) {
                    this.suggestions = [];
                    return;
                }
                
                try {
                    const response = await fetch(
                        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(this.form.location)}&limit=5`,
                        {
                            headers: {
                                'User-Agent': 'MapPosterGenerator/1.0'
                            }
                        }
                    );
                    this.suggestions = await response.json();
                } catch (error) {
                    console.error('Autocomplete error:', error);
                    this.suggestions = [];
                }
            }, 300);
        },
        
        selectLocation(suggestion) {
            this.form.location = suggestion.display_name;
            this.form.latitude = parseFloat(suggestion.lat);
            this.form.longitude = parseFloat(suggestion.lon);
            this.suggestions = [];
            this.showSuggestions = false;
        },
        
        async createPoster() {
            this.loading = true;
            this.error = null;
            
            try {
                // Parse location for city/country if lat/lon not set
                const locationParts = this.form.location.split(',').map(s => s.trim());
                const payload = {
                    city: locationParts[0] || this.form.location,
                    country: locationParts[1] || '',
                    theme: this.form.theme,
                    distance: this.form.distance,
                    latitude: this.form.latitude,
                    longitude: this.form.longitude
                };
                
                const response = await fetch('/api/v1/posters', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    // Redirect to progress page
                    window.location.href = `/generate/${data.job_id}`;
                } else {
                    this.error = data.message || 'Failed to create poster';
                }
            } catch (error) {
                this.error = 'Network error. Please try again.';
            } finally {
                this.loading = false;
            }
        }
    };
}

// Poster Creator Component (Create page)
function posterCreator() {
    return {
        form: {
            location: '',
            theme: 'noir',
            distance: 29000,
            latitude: null,
            longitude: null
        },
        themes: [],
        selectedThemeIds: [],
        suggestions: [],
        showSuggestions: false,
        searchTimeout: null,
        loading: false,
        error: null,
        
        async init() {
            try {
                const response = await fetch('/api/v1/themes');
                const data = await response.json();
                this.themes = data.themes;
                
                // Check for query parameters
                const urlParams = new URLSearchParams(window.location.search);
                
                // Pre-fill location from query params
                const cityParam = urlParams.get('city');
                const countryParam = urlParams.get('country');
                if (cityParam) {
                    // Construct location string
                    this.form.location = countryParam
                        ? `${cityParam}, ${countryParam}`
                        : cityParam;
                }
                
                // Pre-fill distance from query params
                const distanceParam = urlParams.get('distance');
                if (distanceParam) {
                    this.form.distance = parseInt(distanceParam);
                }
                
                // Check for theme query param
                const themeParam = urlParams.get('theme');
                if (themeParam) {
                    this.selectedThemeIds = [themeParam];
                } else if (this.themes.length > 0) {
                    // Select first theme by default
                    this.selectedThemeIds = [this.themes[0].id];
                }
            } catch (error) {
                console.error('Failed to load themes:', error);
            }
        },
        
        toggleTheme(themeId) {
            const index = this.selectedThemeIds.indexOf(themeId);
            if (index > -1) {
                this.selectedThemeIds.splice(index, 1);
            } else {
                this.selectedThemeIds.push(themeId);
            }
        },
        
        selectAllThemes() {
            this.selectedThemeIds = this.themes.map(t => t.id);
        },
        
        deselectAllThemes() {
            this.selectedThemeIds = [];
        },
        
        searchLocation() {
            // Clear previous timeout
            if (this.searchTimeout) {
                clearTimeout(this.searchTimeout);
            }
            
            // Debounce search
            this.searchTimeout = setTimeout(async () => {
                if (this.form.location.length < 3) {
                    this.suggestions = [];
                    return;
                }
                
                try {
                    const response = await fetch(
                        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(this.form.location)}&limit=5`,
                        {
                            headers: {
                                'User-Agent': 'MapPosterGenerator/1.0'
                            }
                        }
                    );
                    this.suggestions = await response.json();
                } catch (error) {
                    console.error('Autocomplete error:', error);
                    this.suggestions = [];
                }
            }, 300);
        },
        
        selectLocation(suggestion) {
            this.form.location = suggestion.display_name;
            this.form.latitude = parseFloat(suggestion.lat);
            this.form.longitude = parseFloat(suggestion.lon);
            this.suggestions = [];
            this.showSuggestions = false;
        },
        
        async createPoster() {
            this.loading = true;
            this.error = null;
            
            try {
                // Parse location for city/country if lat/lon not set
                const locationParts = this.form.location.split(',').map(s => s.trim());
                
                if (this.selectedThemeIds.length > 1) {
                    // Batch mode - multiple themes
                    await this.submitBatchPoster(locationParts);
                } else {
                    // Single theme mode
                    await this.submitSinglePoster(locationParts);
                }
            } catch (error) {
                this.error = 'Network error. Please try again.';
            } finally {
                this.loading = false;
            }
        },
        
        async submitSinglePoster(locationParts) {
            const payload = {
                city: locationParts[0] || this.form.location,
                country: locationParts[1] || '',
                theme: this.selectedThemeIds[0],
                distance: this.form.distance,
                latitude: this.form.latitude,
                longitude: this.form.longitude
            };
            
            const response = await fetch('/api/v1/posters', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Redirect to progress page
                window.location.href = `/generate/${data.job_id}`;
            } else {
                this.error = data.message || 'Failed to create poster';
            }
        },
        
        async submitBatchPoster(locationParts) {
            const payload = {
                city: locationParts[0] || this.form.location,
                country: locationParts[1] || '',
                themes: this.selectedThemeIds,
                distance: this.form.distance,
                latitude: this.form.latitude,
                longitude: this.form.longitude
            };
            
            const response = await fetch('/api/v1/posters/batch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Redirect to batch progress page
                window.location.href = `/batch/${data.batch_id}`;
            } else {
                this.error = data.message || 'Failed to create batch posters';
            }
        },
        
        get canSubmit() {
            return this.form.location &&
                   this.selectedThemeIds.length > 0 &&
                   !this.loading;
        }
    };
}

// Job Monitor Component (Progress page)
function jobMonitor(jobId) {
    return {
        jobId: jobId,
        status: {
            status: 'pending',
            progress: 0,
            current_step: 'Initializing...',
            city: '',
            country: '',
            theme: '',
            created_at: null
        },
        intervalId: null,
        currentTime: Date.now(),
        
        startPolling() {
            // Fetch immediately
            this.fetchStatus();
            
            // Then poll every 2 seconds
            this.intervalId = setInterval(() => {
                this.fetchStatus();
                this.currentTime = Date.now(); // Update current time for elapsed calculation
            }, 2000);
        },
        
        async fetchStatus() {
            try {
                const response = await fetch(`/api/v1/jobs/${this.jobId}`);
                
                if (!response.ok) {
                    throw new Error('Failed to fetch status');
                }
                
                const data = await response.json();
                this.status = data;
                
                // Auto-redirect on completion
                if (data.status === 'completed' && data.result && data.result.poster_id) {
                    if (this.intervalId) {
                        clearInterval(this.intervalId);
                    }
                    // Redirect to result page
                    window.location.href = `/result/${data.result.poster_id}`;
                    return;
                }
                
                // Stop polling if failed or cancelled
                if (data.status === 'failed' || data.status === 'cancelled') {
                    if (this.intervalId) {
                        clearInterval(this.intervalId);
                    }
                }
            } catch (error) {
                console.error('Failed to fetch job status:', error);
            }
        },
        
        async cancelJob() {
            if (!confirm('Are you sure you want to cancel this poster generation?')) {
                return;
            }
            
            try {
                const response = await fetch(`/api/v1/jobs/${this.jobId}/cancel`, {
                    method: 'POST'
                });
                
                if (response.ok) {
                    window.location.href = '/';
                } else {
                    alert('Failed to cancel job');
                }
            } catch (error) {
                console.error('Failed to cancel job:', error);
                alert('Failed to cancel job');
            }
        },
        
        get elapsedTime() {
            if (!this.status.created_at) {
                return '0m 0s';
            }
            
            // Parse the created_at timestamp
            const startTime = new Date(this.status.created_at).getTime();
            const seconds = Math.floor((this.currentTime - startTime) / 1000);
            const mins = Math.floor(seconds / 60);
            const secs = seconds % 60;
            return `${mins}m ${secs}s`;
        }
    };
}

// Batch Monitor Component (Batch Progress page)
function batchMonitor(batchId) {
    return {
        batchId: batchId,
        batchInfo: {
            batch_id: batchId,
            city: '',
            country: '',
            themes: [],
            total_themes: 0
        },
        jobs: [],
        intervalId: null,
        
        startPolling() {
            // Fetch immediately
            this.fetchBatchStatus();
            
            // Then poll every 2 seconds
            this.intervalId = setInterval(() => {
                this.fetchBatchStatus();
            }, 2000);
        },
        
        async fetchBatchStatus() {
            try {
                const response = await fetch(`/api/v1/posters/batch/${this.batchId}/status`);
                
                if (!response.ok) {
                    console.error('Failed to fetch batch status');
                    return;
                }
                
                const data = await response.json();
                this.batchInfo = data;
                this.jobs = data.jobs || [];
                
                // Stop polling if all jobs are done (completed or failed)
                if (this.allCompleted) {
                    if (this.intervalId) {
                        clearInterval(this.intervalId);
                    }
                }
            } catch (error) {
                console.error('Failed to fetch batch status:', error);
            }
        },
        
        get totalThemes() {
            return this.jobs.length || this.batchInfo.total_themes || 0;
        },
        
        get completedCount() {
            return this.jobs.filter(j => j.status === 'completed').length;
        },
        
        get processingCount() {
            return this.jobs.filter(j => j.status === 'processing').length;
        },
        
        get failedCount() {
            return this.jobs.filter(j => j.status === 'failed').length;
        },
        
        get pendingCount() {
            return this.jobs.filter(j => j.status === 'pending').length;
        },
        
        get overallProgress() {
            if (this.totalThemes === 0) return 0;
            
            // Calculate weighted progress
            // completed = 100%, processing = current progress, pending = 0%
            let totalProgress = 0;
            this.jobs.forEach(job => {
                if (job.status === 'completed') {
                    totalProgress += 100;
                } else if (job.status === 'processing') {
                    totalProgress += job.progress || 0;
                } else if (job.status === 'failed') {
                    totalProgress += 100; // Count failed as done for progress calculation
                }
                // pending jobs add 0
            });
            
            return Math.round(totalProgress / this.totalThemes);
        },
        
        get allCompleted() {
            if (this.jobs.length === 0) return false;
            return this.jobs.every(j => j.status === 'completed' || j.status === 'failed');
        }
    };
}

// Make functions globally available for Alpine.js
window.quickCreate = quickCreate;
window.posterCreator = posterCreator;
window.jobMonitor = jobMonitor;
window.batchMonitor = batchMonitor;