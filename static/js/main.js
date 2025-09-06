// Estado Global
let currentBotId = null;
let bots = [];

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Sistema iniciado');
    loadBots();
    setupEventListeners();
});

// Event Listeners
function setupEventListeners() {
    // Fechar modal ao clicar fora
    window.onclick = (event) => {
        if (event.target.classList.contains('modal')) {
            event.target.classList.remove('active');
        }
    };
    
    // Tecla ESC para fechar modais
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeAllModals();
        }
    });
}

// Funções de Modal
function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

function closeAllModals() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.classList.remove('active');
    });
}

// Modal de Adicionar Bot
function openAddBotModal() {
    document.getElementById('addBotForm').reset();
    openModal('addBotModal');
}

// Modal de Configurar Bot
function configureBotModal(botId) {
    currentBotId = botId;
    loadBotConfig(botId);
    openModal('configBotModal');
}

// Notificações
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Utilitários
function formatDate(dateString) {
    if (!dateString) return 'Nunca';
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR') + ' ' + date.toLocaleTimeString('pt-BR');
}

// Adicionar estilos de notificação
const style = document.createElement('style');
style.textContent = `
    .notification {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 4px;
        color: white;
        font-size: 14px;
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.3s ease;
        z-index: 3000;
    }
    
    .notification.show {
        opacity: 1;
        transform: translateX(0);
    }
    
    .notification-success {
        background-color: var(--color-success);
        color: var(--color-secondary);
    }
    
    .notification-error {
        background-color: var(--color-error);
    }
    
    .notification-warning {
        background-color: #ff9800;
    }
`;
document.head.appendChild(style);