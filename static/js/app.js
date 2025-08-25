// Dota TI Helper - Main Application
class DotaTIHelper {
    constructor() {
        this.state = {
            selectedPlayerId: null,
            selectedTeamId: null,
            isAdvancedMode: false
        };
        
        this.elements = {};
        this.init();
    }
    
    init() {
        this.cacheElements();
        this.bindEvents();
        this.initializeApp();
    }
    
    cacheElements() {
        // Cache frequently used DOM elements
        this.elements = {
            leagueSelect: document.getElementById('leagueSelect'),
            teamSelect: document.getElementById('teamSelect'),
            playerSelect: document.getElementById('playerSelect'),
            heroSelect: document.getElementById('heroSelect'),
            statsSection: document.getElementById('statsSection'),
            statsContent: document.getElementById('statsContent'),
            toggleAdvancedBtn: document.getElementById('toggleAdvancedMode'),
            advancedGrid: document.getElementById('advancedSelectionGrid'),
            modeInstructions: document.getElementById('modeInstructions')
        };
        
        // Debug: Log which elements were found
        console.log('Cached elements:', {
            leagueSelect: !!this.elements.leagueSelect,
            teamSelect: !!this.elements.teamSelect,
            playerSelect: !!this.elements.playerSelect,
            heroSelect: !!this.elements.heroSelect,
            statsSection: !!this.elements.statsSection,
            statsContent: !!this.elements.statsContent,
            toggleAdvancedBtn: !!this.elements.toggleAdvancedBtn,
            advancedGrid: !!this.elements.advancedGrid,
            modeInstructions: !!this.elements.modeInstructions
        });
        
        // Check for missing critical elements
        if (!this.elements.leagueSelect) {
            console.error('❌ Critical: leagueSelect element not found!');
        }
        if (!this.elements.teamSelect) {
            console.error('❌ Critical: teamSelect element not found!');
        }
        if (!this.elements.playerSelect) {
            console.error('❌ Critical: playerSelect element not found!');
        }
        if (!this.elements.heroSelect) {
            console.error('❌ Critical: heroSelect element not found!');
        }
    }
    
    bindEvents() {
        console.log('🔗 Binding events...');
        
        // Bind event listeners
        if (this.elements.leagueSelect) {
            this.elements.leagueSelect.addEventListener('change', () => this.onLeagueChange());
            console.log('✅ League select event bound');
        } else {
            console.error('❌ Cannot bind league select event - element not found');
        }
        
        if (this.elements.teamSelect) {
            this.elements.teamSelect.addEventListener('change', () => this.onTeamChange());
            console.log('✅ Team select event bound');
        } else {
            console.error('❌ Cannot bind team select event - element not found');
        }
        
        if (this.elements.playerSelect) {
            this.elements.playerSelect.addEventListener('change', () => this.onPlayerChange());
            console.log('✅ Player select event bound');
        } else {
            console.error('❌ Cannot bind player select event - element not found');
        }
        
        if (this.elements.heroSelect) {
            this.elements.heroSelect.addEventListener('change', () => this.onHeroChange());
            console.log('✅ Hero select event bound');
        } else {
            console.error('❌ Cannot bind hero select event - element not found');
        }
        
        if (this.elements.toggleAdvancedBtn) {
            this.elements.toggleAdvancedBtn.addEventListener('click', () => this.toggleAdvancedMode());
            console.log('✅ Advanced mode toggle event bound');
        } else {
            console.error('❌ Cannot bind advanced mode toggle event - element not found');
        }
        
        // Initialize context switching
        this.initializeContextSwitching();
        console.log('🔗 Event binding complete');
    }
    
    async onLeagueChange() {
        const leagueId = this.elements.leagueSelect.value;
        console.log('League changed to:', leagueId);
        
        if (leagueId) {
            await this.loadTeams(leagueId);
            this.enableHeroSelection();
            await this.loadAllHeroes();
            this.resetDownstreamSelects();
        } else {
            this.disableAllDownstreamSelects();
        }
        
        this.hideStatsSection();
    }
    
    async onTeamChange() {
        const teamId = this.elements.teamSelect.value;
        this.state.selectedTeamId = teamId;
        console.log('Team changed to:', teamId);
        
        if (teamId) {
            await this.loadPlayers(teamId);
            this.enablePlayerSelection();
        } else {
            this.disablePlayerSelection();
        }
        
        this.hideStatsSection();
    }
    
    async onPlayerChange() {
        const playerId = this.elements.playerSelect.value;
        console.log('Player changed to:', playerId);
        
        if (playerId) {
            this.state.selectedPlayerId = playerId;
            await this.loadHeroes(playerId);
            
            if (this.state.isAdvancedMode) {
                this.loadUnifiedVisualization();
            } else {
                this.loadStats();
            }
        } else {
            this.state.selectedPlayerId = null;
            await this.loadAllHeroes();
            this.hideStatsSection();
        }
    }
    
    onHeroChange() {
        const heroId = this.elements.heroSelect.value;
        
        if (heroId) {
            if (this.state.selectedPlayerId) {
                if (this.state.isAdvancedMode) {
                    this.enableAdvancedSelects();
                    this.loadHeroesForAdvancedSelects();
                    this.loadUnifiedVisualization();
                } else {
                    this.loadStats();
                }
            } else {
                if (this.state.isAdvancedMode) {
                    this.loadUnifiedVisualization();
                }
            }
        }
    }
    
    // Data loading methods
    async loadTeams(leagueId) {
        try {
            console.log('Loading teams for league:', leagueId);
            this.showLoadingState(this.elements.teamSelect, 'Loading teams...');
            
            const response = await fetch(`/teams/${leagueId}`);
            const html = await response.text();
            
            this.elements.teamSelect.innerHTML = html;
            this.elements.teamSelect.disabled = false;
            console.log('Teams loaded successfully');
        } catch (error) {
            console.error('Error loading teams:', error);
            this.showErrorState(this.elements.teamSelect, 'Error loading teams');
        }
    }
    
    async loadPlayers(teamId) {
        try {
            console.log('Loading players for team:', teamId);
            this.showLoadingState(this.elements.playerSelect, 'Loading players...');
            
            const response = await fetch(`/players/${teamId}`);
            const html = await response.text();
            
            this.elements.playerSelect.innerHTML = html;
            this.elements.playerSelect.disabled = false;
            console.log('Players loaded successfully');
        } catch (error) {
            console.error('Error loading players:', error);
            this.showErrorState(this.elements.playerSelect, 'Error loading players');
        }
    }
    
    async loadHeroes(playerId) {
        try {
            console.log('Loading heroes for player:', playerId);
            this.showLoadingState(this.elements.heroSelect, 'Loading heroes...');
            
            const response = await fetch(`/heroes/${playerId}`);
            const html = await response.text();
            
            this.elements.heroSelect.innerHTML = html;
            this.elements.heroSelect.disabled = false;
            console.log('Heroes loaded successfully');
        } catch (error) {
            console.error('Error loading heroes:', error);
            this.showErrorState(this.elements.heroSelect, 'Error loading heroes');
        }
    }
    
    async loadAllHeroes() {
        try {
            console.log('Loading all heroes');
            this.showLoadingState(this.elements.heroSelect, 'Loading heroes...');
            
            const response = await fetch('/heroes');
            const html = await response.text();
            
            this.elements.heroSelect.innerHTML = html;
            this.elements.heroSelect.disabled = false;
            console.log('All heroes loaded successfully');
        } catch (error) {
            console.error('Error loading all heroes:', error);
            this.showErrorState(this.elements.heroSelect, 'Error loading heroes');
        }
    }
    
    // Stats loading methods
    async loadStats() {
        if (!this.state.selectedPlayerId) return;
        
        try {
            this.showStatsSection();
            await this.loadStatsForContext('tournament');
        } catch (error) {
            console.error('Error loading stats:', error);
            this.showErrorState(this.elements.statsContent, 'Error loading statistics');
        }
    }
    
    async loadUnifiedVisualization() {
        try {
            this.showStatsSection();
            await this.loadStatsForContext('tournament');
        } catch (error) {
            console.error('Error loading visualization:', error);
            this.showErrorState(this.elements.statsContent, 'Error loading visualization');
        }
    }
    
    async loadStatsForContext(context) {
        const heroId = this.elements.heroSelect.value;
        if (!this.state.selectedPlayerId && !heroId) {
            console.log('No player or hero selected, cannot load context stats');
            return;
        }
        
        console.log('Loading stats for context:', context);
        
        try {
            this.showLoadingState(this.elements.statsContent, `Loading statistics for ${context}...`);
            
            const params = this.buildContextParams(context);
            const url = `/stats/context?${params.toString()}`;
            
            console.log('Loading context stats from:', url);
            
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.success) {
                this.displayContextStats(data.data, context);
            } else {
                this.showErrorState(this.elements.statsContent, `Error loading statistics: ${data.error || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Error loading context stats:', error);
            this.showErrorState(this.elements.statsContent, 'Error loading statistics');
        }
    }
    
    buildContextParams(context) {
        const params = new URLSearchParams();
        params.append('context', context);
        
        const leagueId = this.elements.leagueSelect.value;
        const teamId = this.elements.teamSelect.value;
        
        if (leagueId) params.append('league_id', leagueId);
        if (teamId) params.append('team_id', teamId);
        if (this.state.selectedPlayerId) params.append('player_id', this.state.selectedPlayerId);
        if (this.elements.heroSelect.value) params.append('hero_id', this.elements.heroSelect.value);
        
        return params;
    }
    
    // Display methods
    displayContextStats(statsData, context) {
        console.log('📊 Displaying stats data:', statsData);
        console.log('📊 Context:', context);
        
        if (!statsData || Object.keys(statsData).length === 0) {
            this.elements.statsContent.innerHTML = `<div class="data-message">No data available for ${context} context</div>`;
            return;
        }
        
        let html = '<div class="compact-stats-container">';
        
        if (statsData.player_hero) {
            console.log('🎯 Adding player_hero section:', statsData.player_hero);
            html += this.createStatsSection('🎯 Player + Hero Performance', statsData.player_hero, 'primary');
        }
        
        if (statsData.hero_baseline) {
            console.log('⚔️ Adding hero_baseline section:', statsData.hero_baseline);
            html += this.createStatsSection('⚔️ Hero Baseline Performance', statsData.hero_baseline, 'secondary');
        }
        
        if (statsData.player_overall) {
            console.log('👤 Adding player_overall section:', statsData.player_overall);
            html += this.createStatsSection('👤 Player Overall Performance', statsData.player_overall, 'tertiary');
        }
        
        html += '</div>';
        this.elements.statsContent.innerHTML = html;
    }
    
    createStatsSection(title, stats, priority) {
        let html = `<div class="stats-category ${priority}">`;
        html += `<h3>${title}</h3>`;
        html += '<div class="compact-stats-grid">';
        
        if (stats.last_hits) {
            html += this.createStatCard('Last Hits at 5 min', stats.last_hits, priority);
        }
        
        if (stats.kills) {
            html += this.createStatCard('Kills', stats.kills, priority);
        }
        
        html += '</div></div>';
        return html;
    }
    
    createStatCard(metricName, stats, priority) {
        const priorityClass = priority === 'primary' ? 'primary' : 
                            priority === 'secondary' ? 'secondary' : 
                            priority === 'tertiary' ? 'tertiary' : 'quaternary';
        
        return `
            <div class="stat-card ${priorityClass}">
                <h4>${metricName}</h4>
                <div class="stat-value">${stats.mean.toFixed(1)}</div>
                <div class="stat-label">±${stats.std.toFixed(1)} (${stats.count} games)</div>
                <div class="stat-range">Range: ${stats.min}-${stats.max}</div>
                <div class="stat-quartiles">Q1: ${stats.q25.toFixed(1)} | Q3: ${stats.q75.toFixed(1)}</div>
            </div>
        `;
    }
    
    // Advanced mode methods
    toggleAdvancedMode() {
        this.state.isAdvancedMode = !this.state.isAdvancedMode;
        const btn = this.elements.toggleAdvancedBtn;
        const grid = this.elements.advancedGrid;
        const instructions = this.elements.modeInstructions;
        
        if (this.state.isAdvancedMode) {
            btn.textContent = '🔧 Disable Advanced Mode';
            btn.classList.add('active');
            grid.classList.remove('hidden');
            instructions.classList.remove('hidden');
            
            if (this.elements.heroSelect.value) {
                this.enableAdvancedSelects();
            }
            
            if (this.elements.heroSelect.value || this.hasAdvancedSelections()) {
                this.loadUnifiedVisualization();
            }
        } else {
            btn.textContent = '🔧 Toggle Advanced Analysis Mode';
            btn.classList.remove('active');
            grid.classList.add('hidden');
            instructions.classList.add('hidden');
            
            this.disableAdvancedSelects();
            this.resetAdvancedSelects();
            
            if (this.state.selectedPlayerId) {
                this.loadStats();
            }
        }
    }
    
    hasAdvancedSelections() {
        const friendlyHero = document.getElementById('friendlyHeroSelect');
        const enemyHero1 = document.getElementById('enemyHero1Select');
        const enemyHero2 = document.getElementById('enemyHero2Select');
        
        return (friendlyHero && friendlyHero.value) || 
               (enemyHero1 && enemyHero1.value) || 
               (enemyHero2 && enemyHero2.value);
    }
    
    enableAdvancedSelects() {
        const selects = ['friendlyHeroSelect', 'enemyHero1Select', 'enemyHero2Select', 'sideSelect'];
        selects.forEach(id => {
            const select = document.getElementById(id);
            if (select) select.disabled = false;
        });
    }
    
    disableAdvancedSelects() {
        const selects = ['friendlyHeroSelect', 'enemyHero1Select', 'enemyHero2Select', 'sideSelect'];
        selects.forEach(id => {
            const select = document.getElementById(id);
            if (select) select.disabled = true;
        });
    }
    
    resetAdvancedSelects() {
        const selects = ['friendlyHeroSelect', 'enemyHero1Select', 'enemyHero2Select', 'sideSelect'];
        selects.forEach(id => {
            const select = document.getElementById(id);
            if (select) select.value = '';
        });
    }
    
    // Context switching methods
    initializeContextSwitching() {
        const contextTabs = document.querySelectorAll('.context-tab');
        console.log('Initializing context switching, found tabs:', contextTabs.length);
        
        contextTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const context = tab.dataset.context;
                console.log('Context switched to:', context);
                
                // Update active tab
                contextTabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                // Update context info
                const currentContext = document.getElementById('current-context');
                if (currentContext) {
                    currentContext.textContent = tab.textContent;
                }
                
                // Load stats for the new context
                this.loadStatsForContext(context);
            });
        });
    }
    
    // Utility methods
    showLoadingState(element, message) {
        if (element) {
            element.innerHTML = `<option value="">${message}...</option>`;
            element.disabled = true;
        }
    }
    
    showErrorState(element, message) {
        if (element) {
            element.innerHTML = `<option value="">${message}</option>`;
        }
    }
    
    enableHeroSelection() {
        if (this.elements.heroSelect) {
            this.elements.heroSelect.disabled = false;
        }
    }
    
    enablePlayerSelection() {
        if (this.elements.playerSelect) {
            this.elements.playerSelect.disabled = false;
        }
    }
    
    resetDownstreamSelects() {
        if (this.elements.playerSelect) {
            this.elements.playerSelect.innerHTML = '<option value="">Select a player...</option>';
            this.elements.playerSelect.disabled = true;
        }
        
        this.state.selectedTeamId = null;
        this.state.selectedPlayerId = null;
    }
    
    disableAllDownstreamSelects() {
        const selects = [this.elements.teamSelect, this.elements.playerSelect, this.elements.heroSelect];
        selects.forEach(select => {
            if (select) {
                select.innerHTML = '<option value="">Select...</option>';
                select.disabled = true;
            }
        });
        
        this.state.selectedTeamId = null;
        this.state.selectedPlayerId = null;
    }
    
    disablePlayerSelection() {
        if (this.elements.playerSelect) {
            this.elements.playerSelect.innerHTML = '<option value="">Select a player...</option>';
            this.elements.playerSelect.disabled = true;
        }
        
        this.state.selectedPlayerId = null;
    }
    
    showStatsSection() {
        if (this.elements.statsSection) {
            this.elements.statsSection.classList.remove('hidden');
        }
    }
    
    hideStatsSection() {
        if (this.elements.statsSection) {
            this.elements.statsSection.classList.add('hidden');
        }
    }
    
    // Initialization
    initializeApp() {
        console.log('DOM loaded, checking for default league');
        
        if (this.elements.leagueSelect && this.elements.leagueSelect.value) {
            console.log('Default league found, loading teams and heroes');
            this.onLeagueChange();
        } else {
            console.log('No default league selected');
        }
    }
}

// Initialize the application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new DotaTIHelper();
});
