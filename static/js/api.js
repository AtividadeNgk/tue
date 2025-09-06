// Cliente API
class ApiClient {
    constructor() {
        this.baseUrl = '/api';
    }
    
    async request(method, endpoint, data = null) {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, options);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }
    
    async createBot(token) {
        return this.request('POST', '/bots', { token });
    }
    
    async getBots() {
        return this.request('GET', '/bots');
    }
    
    async getBot(botId) {
        return this.request('GET', `/bots/${botId}`);
    }
    
    async updateBotConfig(botId, config) {
        return this.request('PUT', `/bots/${botId}/config`, config);
    }
    
    async deleteBot(botId) {
        return this.request('DELETE', `/bots/${botId}`);
    }
    
    async getBotStats(botId) {
        return this.request('GET', `/bots/${botId}/stats`);
    }
}

const api = new ApiClient();

// Funções de Bot
async function loadBots() {
    try {
        const response = await api.getBots();
        bots = response.bots;
        updateBotsDisplay();
    } catch (error) {
        showNotification('Erro ao carregar bots', 'error');
    }
}

async function addBot() {
    const token = document.getElementById('botToken').value.trim();
    
    if (!token) {
        showNotification('Por favor, insira o token do bot', 'warning');
        return;
    }
    
    try {
        const response = await api.createBot(token);
        showNotification('Bot adicionado com sucesso!', 'success');
        closeModal('addBotModal');
        loadBots();
    } catch (error) {
        showNotification('Erro ao adicionar bot', 'error');
    }
}

async function loadBotConfig(botId) {
    try {
        const bot = await api.getBot(botId);
        
        document.getElementById('configBotId').value = botId;
        
        // Campos hidden para mídia
        document.getElementById('mediaUrl').value = bot.config.media_url || '';
        document.getElementById('mediaType').value = bot.config.media_type || 'photo';
        
        // Campos visíveis
        document.getElementById('message1').value = bot.config.message_1 || '';
        document.getElementById('message2').value = bot.config.message_2 || '';
        // REMOVIDO: document.getElementById('buttonText').value = bot.config.button_text || 'Ver Planos';
        
        // Mostrar preview se tiver mídia configurada
        const preview = document.getElementById('mediaPreview');
        if (bot.config.media_url) {
            if (bot.config.media_type === 'video') {
                preview.innerHTML = `
                    <div style="margin-top: 10px; padding: 20px; border: 1px solid #333; border-radius: 4px; text-align: center;">
                        <span style="font-size: 48px;">🎥</span>
                        <p style="color: #888; margin-top: 10px;">Vídeo configurado</p>
                    </div>
                `;
            } else {
                preview.innerHTML = `<img src="${bot.config.media_url}" style="max-width: 200px; max-height: 200px; border: 1px solid #333; border-radius: 4px; margin-top: 10px;">`;
            }
        } else {
            preview.innerHTML = '';
        }
        
        loadPlans(bot.config.plans || []);
        
    } catch (error) {
        showNotification('Erro ao carregar configurações', 'error');
    }
}

// Salvar configurações
async function saveConfig() {
    const config = {
        media_url: document.getElementById('mediaUrl').value,
        media_type: document.getElementById('mediaType').value || 'photo',
        message_1: document.getElementById('message1').value,
        message_2: document.getElementById('message2').value,
        // REMOVIDO: button_text: document.getElementById('buttonText').value,
        plans: getPlansFromForm()
    };
    
    try {
        await api.updateBotConfig(currentBotId, config);
        showNotification('Configurações salvas com sucesso!', 'success');
        closeModal('configBotModal');
        loadBots();
    } catch (error) {
        showNotification('Erro ao salvar configurações', 'error');
    }
}

async function deleteBot() {
    if (!confirm('Tem certeza que deseja excluir este bot?')) {
        return;
    }
    
    try {
        await api.deleteBot(currentBotId);
        showNotification('Bot excluído com sucesso!', 'success');
        closeModal('configBotModal');
        loadBots();
    } catch (error) {
        showNotification('Erro ao excluir bot', 'error');
    }
}

async function viewBotStats(botId) {
    try {
        const stats = await api.getBotStats(botId);
        console.log('Estatísticas:', stats);
    } catch (error) {
        showNotification('Erro ao carregar estatísticas', 'error');
    }
}

// Upload de arquivo
async function handleFileUpload(input) {
    const file = input.files[0];
    if (!file) return;
    
    // Validar tamanho (10MB)
    if (file.size > 10 * 1024 * 1024) {
        showNotification('Arquivo muito grande! Máximo 10MB', 'error');
        input.value = '';
        return;
    }
    
    // Criar preview visual apenas
    const preview = document.getElementById('mediaPreview');
    
    if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.innerHTML = `<img src="${e.target.result}" style="max-width: 200px; max-height: 200px; border: 1px solid #333; border-radius: 4px; margin-top: 10px;">`;
        };
        reader.readAsDataURL(file);
    } else if (file.type.startsWith('video/')) {
        // Para vídeo, criar preview com ícone ou thumbnail
        preview.innerHTML = `
            <div style="margin-top: 10px; padding: 20px; border: 1px solid #333; border-radius: 4px; text-align: center;">
                <span style="font-size: 48px;">🎥</span>
                <p style="color: #888; margin-top: 10px;">${file.name}</p>
            </div>
        `;
    }
    
    // Upload do arquivo
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        showNotification('Enviando arquivo...', 'success');
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Erro no upload');
        }
        
        const result = await response.json();
        
        // Preencher campos hidden com URL e tipo
        document.getElementById('mediaUrl').value = result.url;
        document.getElementById('mediaType').value = result.type;
        
        showNotification('Mídia configurada com sucesso!', 'success');
        
    } catch (error) {
        showNotification('Erro ao enviar arquivo', 'error');
        console.error(error);
    }
}

// Gerenciamento de Planos
function loadPlans(plans) {
    const plansList = document.getElementById('plansList');
    plansList.innerHTML = '';
    
    if (!plans || plans.length === 0) return;
    
    plans.forEach((plan) => {
        if (typeof plan === 'string') {
            addPlanField({ name: plan, value: '0', days: '30' });
        } else {
            addPlanField(plan);
        }
    });
}

function addPlanField(plan = null) {
    const plansList = document.getElementById('plansList');
    
    const planItem = document.createElement('div');
    planItem.className = 'plan-item';
    planItem.innerHTML = `
        <div class="plan-item-header">
            <strong>Plano</strong>
            <button type="button" class="btn-remove-plan" onclick="this.parentElement.parentElement.remove()">
                X
            </button>
        </div>
        <div class="plan-fields">
            <div class="plan-field">
                <label>Nome do Plano</label>
                <input type="text" 
                       class="plan-name" 
                       placeholder="Ex: Premium"
                       value="${plan && plan.name ? plan.name : ''}">
            </div>
            <div class="plan-field">
                <label>Valor (R$)</label>
                <input type="text" 
                       class="plan-value" 
                       placeholder="Ex: 29.90"
                       value="${plan && plan.value ? plan.value : ''}">
            </div>
            <div class="plan-field">
                <label>Duração (dias)</label>
                <input type="number" 
                       class="plan-days" 
                       placeholder="Ex: 30"
                       value="${plan && plan.days ? plan.days : ''}">
            </div>
        </div>
    `;
    
    plansList.appendChild(planItem);
}

function getPlansFromForm() {
    const planItems = document.querySelectorAll('.plan-item');
    const plans = [];
    
    planItems.forEach(item => {
        const name = item.querySelector('.plan-name').value.trim();
        const value = item.querySelector('.plan-value').value.trim();
        const days = item.querySelector('.plan-days').value.trim();
        
        if (name && value && days) {
            plans.push({
                name: name,
                value: value,
                days: parseInt(days)
            });
        }
    });
    
    return plans;
}

function updateBotsDisplay() {
    const botsContainer = document.querySelector('.bots-list');
    
    if (!botsContainer) return;
    
    if (bots.length === 0) {
        botsContainer.innerHTML = `
            <div class="empty-state">
                <p>Nenhum bot cadastrado ainda.</p>
                <button class="btn btn-primary" onclick="openAddBotModal()">
                    Adicionar Primeiro Bot
                </button>
            </div>
        `;
    } else {
        botsContainer.innerHTML = bots.map(bot => `
            <div class="bot-card" data-bot-id="${bot.id}">
                <div class="bot-info">
                    <div class="bot-name">@${bot.username || 'Bot sem nome'}</div>
                    <div class="bot-stats">
                        <span>${bot.total_users} usuários</span>
                        <span>${bot.total_messages} mensagens</span>
                    </div>
                </div>
                <div class="bot-actions">
                    <button class="btn-icon" onclick="configureBotModal('${bot.id}')">⚙️</button>
                    <button class="btn-icon" onclick="viewBotStats('${bot.id}')">📊</button>
                </div>
            </div>
        `).join('');
    }
}