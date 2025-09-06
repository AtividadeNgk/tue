// Funções específicas dos modais
function openAddBotModal() {
    document.getElementById('addBotForm').reset();
    openModal('addBotModal');
}

function configureBotModal(botId) {
    currentBotId = botId;
    loadBotConfig(botId);
    openModal('configBotModal');
}

// Adicionar evento ao formulário
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('addBotForm');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await addBot();
        });
    }
});